# Manifest Manager

**Manifest Manager** is a production-grade, transactional Command Line Interface (CLI) for managing hierarchical data (tasks, inventories, project plans) stored in standard XML.

It adheres to the **MVC (Model-View-Controller)** design pattern and ensures data integrity through **atomic transactions**—if an operation fails (e.g., due to a typo), the entire change is rolled back instantly.

## 🚀 Features

* **Transactional Safety:** All edits are atomic. Your data never gets left in a broken state.
* **WYSIWYG Viewing:** The Tree View shows your data exactly as it is stored (case-sensitive).
* **Flexible Search:** Uses standard XPath 1.0 for powerful filtering.
* **Custom Attributes:** Add any key-value pair to any node on the fly.
* **Zero Database:** Stores everything in a portable, human-readable `.xml` file.

## 📦 Installation

### Prerequisites

* Python 3.8+
* `lxml` library

### Setup

1. Clone or download this repository.

2. Install in "editable" mode (recommended):
   
   ```bash
   pip install -e .
   ```

3. Run the tool:
   
   ```bash
   manifest
   ```

## ⚡ Quick Start

1. **Start the Shell**
   
   ```bash
   manifest
   ```

2. **Load/Create a File**
   
   ```text
   (manifest) load my_todo
   ```
   
   *Creates `my_todo.xml` if it doesn't exist.*

3. **Add Data**
   
   ```text
   (my_todo.xml) add --tag project --topic "Garage Cleanup"
   (my_todo.xml) add --tag task --parent "//*[@topic='Garage Cleanup']" --status active "Buy shelving"
   ```

4. **View Data**
   
   ```text
   (my_todo.xml) list
   ```

## 🧪 Development

To run the test suite (requires `pytest`):

```bash
pytest tests
