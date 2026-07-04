# EXO Plugins

Drop plugin packages into this directory. Each plugin is a folder containing:

```
my-plugin/
├── plugin.json    # manifest: name, version, entry point, declared capabilities
└── __init__.py    # entry module exposing register(plugin_api)
```

Plugins are discovered and validated by the `PluginManager` at backend startup
(implemented in Milestone 6). Plugins may only access capabilities they declare
in their manifest (e.g. `tools`, `routes`).
