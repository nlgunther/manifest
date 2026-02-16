"""
DataFrame Conversion Module for Manifest Manager

This module provides direct conversion between XML trees and pandas DataFrames
without requiring file I/O. Users can work with DataFrames in memory and
optionally save to CSV.

Key Features:
    - Direct tree → DataFrame conversion (no temporary files)
    - Works with any subtree or search results
    - Automatic wrapping of search results under <results> node
    - Roundtrip conversion (DataFrame → tree)
    - Zero coupling to pandas internals (users apply their own transformations)

Design Philosophy:
    - Separation of concerns: Conversion != Persistence
    - DRY: DataFrame is the lingua franca between formats
    - Extensibility: Users compose pandas pipelines, not us
    - Simplicity: Clean data in, clean data out
"""

import uuid
import copy
from typing import Optional, Union
import pandas as pd
from lxml import etree


def to_dataframe(
    node: etree.Element,
    *,
    include_text: bool = True,
    generate_ids: bool = True
) -> pd.DataFrame:
    """
    Convert XML tree or subtree to pandas DataFrame.
    
    This is the core conversion function. It walks the tree depth-first
    and extracts all node data into a flat DataFrame structure with
    parent-child relationships preserved via parent_id column.
    
    Args:
        node: Root element of tree or subtree to convert
        include_text: Include element text content in 'text' column
        generate_ids: Auto-generate IDs for nodes without an 'id' attribute
    
    Returns:
        DataFrame with columns:
            - id: Node identifier (from attribute or generated)
            - parent_id: ID of parent node (or 'root' for top-level)
            - tag: Element tag name
            - text: Element text content (if include_text=True)
            - [all other attributes as columns]
    
    Column Order:
        Core columns (id, parent_id, tag, text) appear first,
        followed by all discovered attributes in alphabetical order.
    
    Examples:
        >>> # Convert entire manifest
        >>> df = to_dataframe(repo.tree.getroot())
        >>> 
        >>> # Convert specific subtree
        >>> project = repo.tree.xpath("//project[@id='p1']")[0]
        >>> df = to_dataframe(project)
        >>> 
        >>> # Convert search results (wrap first)
        >>> tasks = repo.tree.xpath("//task[@status='active']")
        >>> container = etree.Element('results')
        >>> for task in tasks:
        >>>     container.append(task)
        >>> df = to_dataframe(container)
    
    Notes:
        - Generates unique IDs for nodes without 'id' attribute if generate_ids=True
        - Parent-child relationships preserved via parent_id column
        - All attributes become DataFrame columns
        - Text content optional (can be large for some documents)
        - Returns empty DataFrame if node has no children and no data
    """
    def collect(elem: etree.Element, parent_id: str = 'root'):
        """
        Generator that yields (node_data_dict) for each element in tree.
        
        Uses depth-first traversal to maintain natural document order.
        Each node becomes one row in the final DataFrame.
        """
        # Get or generate node ID
        node_id = elem.get('id')
        if not node_id and generate_ids:
            node_id = f"node_{uuid.uuid4().hex[:8]}"
            elem.set('id', node_id)  # Store for consistency
        elif not node_id:
            node_id = f"anon_{id(elem)}"  # Fallback using memory address
        
        # Build row data starting with core columns
        row = {
            'id': node_id,
            'parent_id': parent_id,
            'tag': elem.tag,
        }
        
        # Add text content if requested and present
        if include_text and elem.text:
            text = elem.text.strip()
            if text:  # Only include non-empty text
                row['text'] = text
        
        # Add all attributes (except 'id' which we already have)
        for key, value in elem.attrib.items():
            if key != 'id':
                row[key] = value
        
        yield row
        
        # Recurse on children
        for child in elem:
            # Skip comments and processing instructions
            if isinstance(child.tag, str):
                yield from collect(child, parent_id=node_id)
    
    # Collect all rows
    rows = list(collect(node))
    
    if not rows:
        # Return empty DataFrame with expected structure
        return pd.DataFrame(columns=['id', 'parent_id', 'tag', 'text'])
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Ensure column order: core columns first, then alphabetical attributes
    core_cols = ['id', 'parent_id', 'tag', 'text']
    existing_core = [c for c in core_cols if c in df.columns]
    attribute_cols = sorted([c for c in df.columns if c not in core_cols])
    df = df[existing_core + attribute_cols]
    
    return df


def find_to_dataframe(
    tree: Union[etree.ElementTree, etree.Element],
    xpath: str,
    *,
    wrap_tag: str = 'results',
    **kwargs
) -> pd.DataFrame:
    """
    Execute XPath query and convert results to DataFrame.
    
    This is a convenience wrapper around to_dataframe() that handles
    the common pattern of searching for nodes and wanting them as a DataFrame.
    Automatically wraps results under a container node for consistent structure.
    
    Args:
        tree: ElementTree or Element to search
        xpath: XPath expression to execute
        wrap_tag: Tag name for container node (default: 'results')
        **kwargs: Additional arguments passed to to_dataframe()
    
    Returns:
        DataFrame containing all matched nodes
        (Empty DataFrame if no matches)
    
    Examples:
        >>> # Find all high-priority tasks
        >>> df = find_to_dataframe(repo.tree, "//task[@priority='high']")
        >>> 
        >>> # Find overdue items
        >>> df = find_to_dataframe(repo.tree, "//*[@status='overdue']")
        >>> 
        >>> # Custom wrapper tag
        >>> df = find_to_dataframe(repo.tree, "//milestone", wrap_tag='search_results')
    
    Notes:
        - Results are wrapped under a container node (<results> by default)
        - Original tree is not modified (deep copies are made)
        - Returns empty DataFrame if XPath matches nothing
        - All kwargs are passed through to to_dataframe()
    """
    # Get tree root if we have an ElementTree
    if isinstance(tree, etree.ElementTree):
        tree = tree.getroot()
    
    # Execute XPath query
    matches = tree.xpath(xpath)
    
    if not matches:
        return pd.DataFrame(columns=['id', 'parent_id', 'tag', 'text'])
    
    # Wrap results under container node
    # Use deep copy to avoid modifying original tree
    container = etree.Element(wrap_tag)
    for match in matches:
        container.append(copy.deepcopy(match))
    
    # Convert to DataFrame
    return to_dataframe(container, **kwargs)


def from_dataframe(
    df: pd.DataFrame,
    root_tag: str = 'root',
    *,
    text_column: str = 'text',
    validate: bool = True
) -> etree.Element:
    """
    Convert DataFrame back to XML tree structure.
    
    Uses branch-stack algorithm for efficient reconstruction of hierarchy
    from flat DataFrame structure. This enables round-trip workflows:
    export → transform → import.
    
    Args:
        df: DataFrame with required columns (id, parent_id, tag)
        root_tag: Tag name for root element
        text_column: Column containing element text (default: 'text')
        validate: Validate required columns are present
    
    Returns:
        Root element of reconstructed tree
    
    Required Columns:
        - id: Node identifier
        - parent_id: Parent node identifier
        - tag: Element tag name
    
    Optional Columns:
        - text: Element text content
        - [any other columns become attributes]
    
    Examples:
        >>> # Round-trip workflow
        >>> df = to_dataframe(tree)
        >>> df.loc[df['status'] == 'pending', 'status'] = 'in_progress'
        >>> new_tree = from_dataframe(df)
        >>> 
        >>> # With custom root
        >>> tree = from_dataframe(df, root_tag='manifest')
    
    Notes:
        - Assumes DataFrame rows are in valid tree order
          (parents before children for best results)
        - Missing parent_id values are treated as root-level nodes
        - Handles NaN values gracefully (converts to empty string or skips)
        - Non-required columns become element attributes
    
    Algorithm:
        Uses a node_map to track created elements by ID, enabling
        efficient parent lookup without tree traversal.
    """
    # Validate required columns
    if validate:
        required = {'id', 'parent_id', 'tag'}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"DataFrame missing required columns: {missing}")
    
    # Check if first row is the actual root (parent_id == 'root')
    # If so, use it as the root instead of creating a container
    root = None
    node_map = {}
    first_row = True
    
    # Process each row
    for _, row in df.iterrows():
        parent_id = row.get('parent_id', 'root')
        if pd.isna(parent_id):
            parent_id = 'root'
        
        tag = row['tag']
        if pd.isna(tag):
            continue  # Skip rows with missing tag
        
        # Build attributes dictionary
        # Exclude core columns that have special handling
        exclude_cols = {'id', 'parent_id', 'tag', text_column}
        attrs = {
            k: str(v) 
            for k, v in row.items() 
            if pd.notna(v) and k not in exclude_cols
        }
        
        # Special handling for first row if it's the root
        if first_row and parent_id == 'root':
            # First row is the root - use it directly
            root = etree.Element(str(tag), attrib=attrs)
            
            # Set ID if present
            if 'id' in row and pd.notna(row['id']):
                root.set('id', str(row['id']))
                node_map[str(row['id'])] = root
            
            # Set text content
            if text_column in row and pd.notna(row[text_column]):
                root.text = str(row[text_column])
            
            # Mark root in node_map for children
            node_map['root'] = root
            first_row = False
            continue
        
        first_row = False
        
        # Create root container if we didn't find it in first row
        if root is None:
            root = etree.Element(root_tag)
            node_map['root'] = root
        
        # Find parent
        if parent_id == 'root':
            parent = root
        else:
            parent = node_map.get(parent_id, root)
        
        # Create element
        elem = etree.SubElement(parent, str(tag), attrib=attrs)
        
        # Set ID attribute
        if 'id' in row and pd.notna(row['id']):
            elem.set('id', str(row['id']))
            node_map[str(row['id'])] = elem  # Track for children
        
        # Set text content
        if text_column in row and pd.notna(row[text_column]):
            elem.text = str(row[text_column])
    
    # If no root was created (empty DataFrame), create default root
    if root is None:
        root = etree.Element(root_tag)
    
    return root


def preview_dataframe(df: pd.DataFrame, max_rows: int = 10) -> str:
    """
    Generate a formatted preview of DataFrame for CLI display.
    
    Args:
        df: DataFrame to preview
        max_rows: Maximum rows to show
    
    Returns:
        Formatted string suitable for console output
    """
    if df.empty:
        return "Empty DataFrame"
    
    # Build summary
    lines = [
        f"DataFrame: {len(df)} rows × {len(df.columns)} columns",
        f"Columns: {', '.join(df.columns.tolist())}",
    ]
    
    # Tag distribution if 'tag' column exists
    if 'tag' in df.columns:
        tag_counts = df['tag'].value_counts()
        lines.append(f"Tags: {', '.join(f'{tag}({count})' for tag, count in tag_counts.items())}")
    
    # Show preview
    lines.append("\nPreview:")
    lines.append(str(df.head(max_rows)))
    
    if len(df) > max_rows:
        lines.append(f"\n... ({len(df) - max_rows} more rows)")
    
    return '\n'.join(lines)
