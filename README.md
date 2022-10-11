# sd-embeddings-sync

Security-focused package manager for huggingface/third-party stable diffusion embeddings.

Install it as a pip package (coming soon) and a command-line tool.

-------------------

## Changelog

### 0.1a - Initial release

- This is the initial release of the script that was brought to saber7ooth by Moonwing from another author.  We do not know the origin of the script.

### 0.2a - saber7ooth's release

- This is the version of the script that was improved by saber7ooth.

### 0.3a - DeityDurg's (unfinished) release

- Starting with this Github repository with:
  - formal documentation applied
  - software license
  - as pip module
  - include unit tests
  - managed by GitHub workflows
  - command-line tool
  - pip package

- this is DeityDurg's dragonified / maintained pip module version of the script.  Changes from here will be moving forward.

- You can't install this yet as its unfinished.  Coming soon(tm)

-------------------

## Package Features

- Embeddings tracking database in ``embeddings.json``, running the file the first time automatically creates the database.
- Pickle scanner to detect mallicious pickle ACE (Arbritrary Code Execution) exploit injections with [picklescan](https://github.com/mmaitre314/picklescan)
- ClamAV-based [pyclamd](https://pypi.org/project/pyClamd/) antivirus scanner to detect mallicious malware in embedding downloads
- Bad actor logging and blacklisting (kill them with dragonfire 🔥)
- Clean, single-file implementation to allow including huggingface embeddings in your experiments

-------------------

## Repository Features

- Github workflows support
- Code standardization with [black](https://github.com/psf/black)
- Code linting with [flake8](https://github.com/PyCQA/flake8)
- Code security testing with CodeQL Analysers

-------------------

## Why not safeunpickle?

safeunpickle is a tool that allows you to attempt to unpack pickle files that may contain valnurabilities.  Unfortunately, its not all the way secure, and there are ways to unpack malicious payloads using it, anyway.

The idea here is to log bad actors and blacklist them when the attempt is made.  This is a less-gray solution and a more black and white (kill it with fire 🔥) approach to the same issue, and allows the owner of the package manager software (you!) to log/identify bad actors/individuals you should not be downloading from.

sdembeddingsync scans and detect vulnerability exploits injected into stable-diffusion embeddings with a 2-factor system ([picklescan](https://github.com/mmaitre314/picklescan) and [pyclamd](https://pypi.org/project/pyClamd/)), block the download and keep a log of where bad downloads where found in the package manager database.

-------------------

## As a service

You can crontab the command-line tool and have it syncing embeddings nightly with no worry that your system will be picking up malware.  Tracking features ensure minimal bandwidth hits to huggingface and third-party embeddings directories themselves.

-------------------

## License

Please visit [here](./LICENSE.md) for a copy of the repository's software license. 

-------------------

## Contributing

Please visit [here](./CONTRIBUTING.md) to review contributing guidelines.