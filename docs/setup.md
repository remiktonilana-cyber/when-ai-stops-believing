# Local environment setup

Run commands from the repository root after cloning or downloading the repository.
The offline Urban Traffic demo uses only the Python standard library. Python 3.9
is the tested baseline; no provider credentials or SDKs are needed for the demo.

```sh
python -m applications.urban_traffic.run_demo --output-dir /tmp/urban-traffic-demo
```

Open the generated `index.html`. You can use `demo-output/` instead of the
temporary directory; that repository-root output directory is ignored by Git.
Arbitrary custom output directories are not automatically ignored.

## Full offline test suite

Use CPython 3.9 on macOS or Linux for the tested environment. The checkpoint
runner imports the Unix-only standard-library module `fcntl`; the full suite
is not presented as native-Windows compatible. The demo does not use `fcntl`.

Create an isolated environment, install the manifest, then run tests:

```sh
python3.9 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

[requirements.txt](../requirements.txt) pins the six direct packages to versions
tested in the repository's existing Python 3.9 environment. NumPy, pandas, SciPy,
scikit-learn, and statsmodels support scientific modules exercised by the suite;
pytest is the test runner. Standard-library modules are not pip dependencies.
This is a direct-dependency manifest, not a complete transitive lockfile or a
claim that other Python/package combinations have been validated.

Installation normally needs package-index access or a prepopulated local wheel
cache. Running the demo and tests needs no provider API calls. Provider tests use
fake transports or mocks.

## Optional provider-backed research

The HTTP providers use standard-library urllib rather than requiring a provider
SDK. Real provider execution needs separately configured credentials and network
access. The Codex provider needs an authenticated external CLI. None of these is
required for the offline demo or full automated test suite.

See the [research index](README.md) and the root README's preserved benchmark
instructions for experiment-specific protocols. Do not put credentials in tracked
files. Local `.env` files are ignored; ignoring a file does not configure or load
it automatically. Local diagnostic text logs are ignored, while scientific
reports and frozen specifications remain tracked and unchanged.
