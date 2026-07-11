# API Reference

The Dashboard runs on FastAPI and exposes the following controls:

* \POST /api/processes/{name}/start\: Boots the process (daemon/proxy)
* \POST /api/processes/{name}/stop\: Hard kills the process
