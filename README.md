# arches-he-sysref-funcs

A small Arches extension app providing additional system reference functions for Arches-based projects. Designed for easy integration with Arches projects (Historic England context).

## Requirements

- Python 3.10+
- Arches >=7.6.6, <7.7.0

Some elements of this app are designed to work with Historic England's specific data model and may not be suitable for other projects without modification.

## Using This App in Your Arches Project

Follow these steps to add `arches-he-sysref-funcs` to your Arches project:

## 1. Install the App

- **For development (standard):**

  ```bash
  pip install -e /path/to/this/app
  ```

- **For development (using included arches-container configuration):**

  This repository includes an `arches-containers` project configuration, so you can import, activate, and start the system as follows:

  1. Ensure Docker is installed and running.
  2. Navigate to your workspace directory (the root where your projects and containers live).
  3. Import the arches-container project configuration:

     ```bash
     act import -p arches_he_sysref_funcs
     ```

  4. Activate the project:

     ```bash
     act activate -p arches_he_sysref_funcs
     ```

  5. Start the system:

     ```bash
     act up
     ```

  6. Once setup and webpack builds are complete, open a browser and navigate to `http://localhost:8002` or use `act view` in a termainal to open the project in your default browser.

  For more details, see the [arches-containers documentation](../arches-containers/readme.md).

- **For production:**

  Add the following to your `pyproject.toml` dependencies (in the `[project]` section):

  ```toml
  arches-he-sysref-funcs @ git+https://github.com/HistoricEngland/arches-he-sysref-funcs.git@release/1.0.0
  ```

  Example:

  ```toml
  dependencies = [
      "arches>=7.6.6,<7.7.0",
      "arches-he-sysref-funcs @ git+https://github.com/HistoricEngland/arches-he-sysref-funcs.git@release/1.0.0",
  ]
  ```

## 2. Update `settings.py`

Add the following to the appropriate locations:

```python
DATATYPE_LOCATIONS.append("arches_he_sysref_funcs.datatypes")
FUNCTION_LOCATIONS.append("arches_he_sysref_funcs.functions")
SEARCH_COMPONENT_LOCATIONS.append("arches_he_sysref_funcs.search.components")
```

Add to `INSTALLED_APPS` and `ARCHES_APPLICATIONS`:

```python
INSTALLED_APPS = (
    ...
    "your_project",
    "arches_he_sysref_funcs",
)
ARCHES_APPLICATIONS = ("arches_he_sysref_funcs",)
```

## 3. Update `urls.py`

Include the app's URLs (add project URLs before this):

```python
urlpatterns = [
    # ... your project urls ...
    path("", include("arches_he_sysref_funcs.urls")),
]
```

## 4. Run Database Migrations

```bash
python manage.py migrate
```

## 5. Install and Build Front-End Dependencies

From the directory containing your `package.json`:

```bash
npm install
npm run build_development
```

## 6. Start Your Arches Project

```bash
python manage.py runserver
```

---

## Usage Example

After installation and configuration, use the provided functions in your Arches project as described above. For example, to run migrations:

```bash
python manage.py migrate
```

---

## License

This project is licensed under the GNU AGPLv3. See the LICENSE file for details.

---

For more information on deploying your Arches project, see the [Arches Deployment Guide](https://arches.readthedocs.io/en/stable/deployment/).
