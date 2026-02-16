"""
DataFrame Commands Module for Manifest Manager

This module provides DataFrame conversion commands as a separate, cleanly-
decoupled module that can be imported into the main shell.

Commands:
    - to_df: Convert tree/subtree to DataFrame
    - find_df: Search and convert to DataFrame  
    - from_df: Import DataFrame from CSV

Usage:
    In manifest.py, add at end of ManifestShell class definition:
    
    ```python
    from .dataframe_commands import add_dataframe_commands
    
    # At end of __init__:
    add_dataframe_commands(self)
    ```

Design:
    - No inheritance, just function injection
    - Clean separation from main shell
    - Optional dependency (gracefully degrades without pandas)
    - Self-contained with own error handling
"""

import os
import shlex


def add_dataframe_commands(shell):
    """
    Add DataFrame commands to ManifestShell instance.
    
    This function dynamically adds three methods to the shell:
        - do_to_df: Convert tree to DataFrame
        - do_find_df: Search and convert  
        - do_from_df: Import from CSV
    
    Args:
        shell: ManifestShell instance
    
    Example:
        >>> from manifest_manager.manifest import ManifestShell
        >>> from manifest_manager.dataframe_commands import add_dataframe_commands
        >>> 
        >>> shell = ManifestShell()
        >>> add_dataframe_commands(shell)
        >>> # Now shell.do_to_df, etc. are available
    """
    # Check if pandas and conversion module are available
    try:
        from .dataframe_conversion import to_dataframe, find_to_dataframe, from_dataframe
        import pandas as pd
        DATAFRAME_AVAILABLE = True
    except ImportError:
        DATAFRAME_AVAILABLE = False
    
    # Helper to show unavailable message
    def _unavailable_message():
        print("Error: DataFrame support requires pandas and dataframe_conversion module")
        print("Install: pip install pandas")
    
    
    # =========================================================================
    # COMMAND: to_df
    # =========================================================================
    
    def do_to_df(self, arg):
        """Convert manifest to DataFrame: to_df [--root <xpath>] [--save <file>] [--no-text]
        
        Convert tree or subtree to pandas DataFrame for analysis.
        Optionally save to CSV file.
        
        SYNTAX:
            to_df [OPTIONS]
        
        OPTIONS:
            --root <xpath>      XPath to subtree (default: /* = all)
            --save <file>       Save to CSV file (optional)
            --no-text          Exclude text content (faster)
            --no-preview       Skip preview display
        
        EXAMPLES:
            # Preview entire manifest
            to_df
            
            # Save to CSV
            to_df --save tasks.csv
            
            # Convert specific project
            to_df --root "//project[@id='p1']" --save project.csv
            
            # Exclude text for large trees
            to_df --no-text --save fast.csv
        
        OUTPUT:
            DataFrame with columns:
                - id: Node identifier
                - parent_id: Parent node ID
                - tag: Element tag name
                - text: Element text (if --no-text not used)
                - [all attributes as columns]
        
        WORKFLOW:
            1. to_df --save tasks.csv
            2. # Edit in pandas/Excel
            3. from_df tasks_updated.csv
        
        SEE ALSO:
            find_df, from_df
        """
        if not DATAFRAME_AVAILABLE:
            _unavailable_message()
            return
        
        # Use existing SafeParser from shell
        if hasattr(self, '_make_parser'):
            p = self._make_parser('to_df')
        else:
            # Fallback: create inline
            import argparse
            p = argparse.ArgumentParser(prog='to_df')
        
        p.add_argument('--root', default='/*', help='XPath to subtree')
        p.add_argument('--save', help='Save to CSV file')
        p.add_argument('--no-text', action='store_true', help='Exclude text content')
        p.add_argument('--no-preview', action='store_true', help='Skip preview')
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            
            if not self.repo.tree:
                print("Error: No manifest loaded")
                return
            
            # Get subtree
            nodes = self.repo.tree.xpath(args.root)
            if not nodes:
                print(f"Error: No nodes found at {args.root}")
                return
            
            # Convert to DataFrame
            try:
                df = to_dataframe(nodes[0], include_text=not args.no_text)
            except Exception as e:
                print(f"Error converting to DataFrame: {e}")
                return
            
            # Save if requested
            if args.save:
                try:
                    df.to_csv(args.save, index=False)
                    print(f"✓ Saved {len(df)} rows to {args.save}")
                except Exception as e:
                    print(f"Error saving CSV: {e}")
                    return
            
            # Show preview
            if not args.no_preview:
                print(f"DataFrame: {len(df)} rows × {len(df.columns)} columns")
                if 'tag' in df.columns:
                    tag_counts = df['tag'].value_counts()
                    print(f"Tags: {', '.join(f'{tag}({count})' for tag, count in tag_counts.items())}")
                print("\nPreview:")
                print(df.head(10))
            elif not args.save:
                print(f"DataFrame: {len(df)} rows × {len(df.columns)} columns")
        
        # Use shell's _exec if available, otherwise direct execution
        if hasattr(self, '_exec'):
            self._exec(_run)
        else:
            try:
                _run()
            except Exception as e:
                print(f"Error: {e}")
    
    
    # =========================================================================
    # COMMAND: find_df
    # =========================================================================
    
    def do_find_df(self, arg):
        """Find nodes and convert to DataFrame: find_df <xpath> [--save <file>]
        
        Execute XPath query and get results as DataFrame.
        Results are automatically wrapped under <results> node.
        
        SYNTAX:
            find_df <xpath> [OPTIONS]
        
        ARGUMENTS:
            xpath               XPath expression to execute
        
        OPTIONS:
            --save <file>       Save results to CSV
            --no-text          Exclude text content
            --no-preview       Skip preview display
        
        EXAMPLES:
            # Find active tasks
            find_df "//task[@status='active']"
            
            # Find and save high-priority items
            find_df "//task[@priority='high']" --save urgent.csv
            
            # Find overdue items
            find_df "//*[@status='overdue']"
        
        OUTPUT:
            DataFrame with all matched nodes.
            Empty DataFrame if no matches (not an error).
        
        WORKFLOW:
            # Export search results
            find_df "//task[@status='active']" --save active.csv
            
            # Edit in pandas
            import pandas as pd
            df = pd.read_csv('active.csv')
            df['status'] = 'in_progress'
            df.to_csv('updated.csv', index=False)
            
            # Re-import
            from_df updated.csv
        
        SEE ALSO:
            to_df, from_df, find
        """
        if not DATAFRAME_AVAILABLE:
            _unavailable_message()
            return
        
        if hasattr(self, '_make_parser'):
            p = self._make_parser('find_df')
        else:
            import argparse
            p = argparse.ArgumentParser(prog='find_df')
        
        p.add_argument('xpath', help='XPath expression')
        p.add_argument('--save', help='Save to CSV')
        p.add_argument('--no-text', action='store_true', help='Exclude text')
        p.add_argument('--no-preview', action='store_true', help='Skip preview')
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            
            if not self.repo.tree:
                print("Error: No manifest loaded")
                return
            
            # Execute search and convert
            try:
                df = find_to_dataframe(
                    self.repo.tree,
                    args.xpath,
                    include_text=not args.no_text
                )
            except Exception as e:
                print(f"Error executing search: {e}")
                return
            
            if df.empty:
                print(f"No matches found for: {args.xpath}")
                return
            
            # Save if requested
            if args.save:
                try:
                    df.to_csv(args.save, index=False)
                    print(f"✓ Saved {len(df)} matching nodes to {args.save}")
                except Exception as e:
                    print(f"Error saving CSV: {e}")
                    return
            
            # Show preview
            if not args.no_preview:
                print(f"Found {len(df)} matches for: {args.xpath}")
                print(f"\nDataFrame: {len(df)} rows × {len(df.columns)} columns")
                if 'tag' in df.columns:
                    tag_counts = df['tag'].value_counts()
                    print(f"Tags: {', '.join(f'{tag}({count})' for tag, count in tag_counts.items())}")
                print("\nPreview:")
                print(df.head(10))
            elif not args.save:
                print(f"Found {len(df)} matches")
        
        if hasattr(self, '_exec'):
            self._exec(_run)
        else:
            try:
                _run()
            except Exception as e:
                print(f"Error: {e}")
    
    
    # =========================================================================
    # COMMAND: from_df
    # =========================================================================
    
    def do_from_df(self, arg):
        """Import DataFrame from CSV: from_df <file> [--parent <xpath>] [--dry-run]
        
        Import CSV file back into manifest.
        Supports round-trip editing workflows.
        
        SYNTAX:
            from_df <file> [OPTIONS]
        
        ARGUMENTS:
            file                CSV file to import
        
        OPTIONS:
            --parent <xpath>    Parent node for imports (default: /*)
            --replace          Replace parent's children
            --dry-run          Preview without modifying
        
        REQUIRED CSV COLUMNS:
            - id: Node identifier
            - parent_id: Parent node ID
            - tag: Element tag name
        
        OPTIONAL CSV COLUMNS:
            - text: Element text content
            - [any other columns become attributes]
        
        EXAMPLES:
            # Import into root
            from_df tasks.csv
            
            # Import under specific parent
            from_df tasks.csv --parent "//project[@id='p1']"
            
            # Replace existing children
            from_df tasks.csv --parent "//milestone[@id='m1']" --replace
            
            # Preview first
            from_df tasks.csv --dry-run
        
        WORKFLOW:
            1. to_df --save original.csv
            2. # Edit in pandas/Excel
            3. from_df edited.csv --dry-run  # Preview
            4. from_df edited.csv            # Apply
            5. save
        
        SEE ALSO:
            to_df, find_df
        """
        if not DATAFRAME_AVAILABLE:
            _unavailable_message()
            return
        
        if hasattr(self, '_make_parser'):
            p = self._make_parser('from_df')
        else:
            import argparse
            p = argparse.ArgumentParser(prog='from_df')
        
        p.add_argument('file', help='CSV file to import')
        p.add_argument('--parent', default='/*', help='Parent XPath')
        p.add_argument('--replace', action='store_true', help='Replace children')
        p.add_argument('--dry-run', action='store_true', help='Preview only')
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            
            if not self.repo.tree:
                print("Error: No manifest loaded")
                return
            
            # Load CSV
            csv_path = args.file
            if not os.path.exists(csv_path):
                print(f"Error: File not found: {csv_path}")
                return
            
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                print(f"Error reading CSV: {e}")
                return
            
            # Validate columns
            required = {'id', 'parent_id', 'tag'}
            missing = required - set(df.columns)
            if missing:
                print(f"Error: CSV missing required columns: {missing}")
                print(f"Required: {required}")
                print(f"Found: {set(df.columns)}")
                return
            
            # Find parent
            parent_nodes = self.repo.tree.xpath(args.parent)
            if not parent_nodes:
                print(f"Error: No nodes found at: {args.parent}")
                return
            parent = parent_nodes[0]
            
            # Convert DataFrame to tree
            try:
                imported_tree = from_dataframe(df)
            except Exception as e:
                print(f"Error converting DataFrame: {e}")
                return
            
            # Show preview
            print(f"Importing {len(df)} nodes from {csv_path}")
            if 'tag' in df.columns:
                tag_counts = df['tag'].value_counts()
                print(f"Tags: {', '.join(f'{tag}({count})' for tag, count in tag_counts.items())}")
            
            if args.dry_run:
                print("\n[DRY RUN - No changes made]")
                print(f"Would import under: {args.parent}")
                if args.replace:
                    print(f"Would replace {len(parent)} existing children")
                else:
                    print(f"Would append to {len(parent)} existing children")
                return
            
            # Apply import
            if args.replace:
                for child in list(parent):
                    parent.remove(child)
                print(f"Removed existing children from {parent.tag}")
            
            # Append imported nodes (skip the artificial root)
            for child in imported_tree:
                parent.append(child)
            
            print(f"✓ Imported {len(imported_tree)} nodes")
            print(f"  Parent now has {len(parent)} children")
        
        if hasattr(self, '_exec'):
            self._exec(_run)
        else:
            try:
                _run()
            except Exception as e:
                print(f"Error: {e}")
    
    
    # =========================================================================
    # INJECT METHODS INTO SHELL
    # =========================================================================
    
    # Bind methods to shell instance
    import types
    shell.do_to_df = types.MethodType(do_to_df, shell)
    shell.do_find_df = types.MethodType(do_find_df, shell)
    shell.do_from_df = types.MethodType(do_from_df, shell)
    
    # Optionally add help shortcuts
    shell.help_to_df = types.MethodType(lambda self: print(do_to_df.__doc__), shell)
    shell.help_find_df = types.MethodType(lambda self: print(do_find_df.__doc__), shell)
    shell.help_from_df = types.MethodType(lambda self: print(do_from_df.__doc__), shell)
