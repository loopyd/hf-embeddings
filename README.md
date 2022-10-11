# sd-embeddings-sync

Package manager for huggingface embeddings, designed for [AUTOMATIC1111](https://github.com/AUTOMATIC1111/stable-diffusion-webuiv)'s repository.

-------------------

## Changelog

### 0.1a - Initial release

- This is the initial release of the script that was brought to saber7ooth by Moonwing from another author.  We do not know the origin of the script.

### 0.2a - saber7ooth's release

- This is the version of the script that was improved by saber7ooth.

### 0.3a - DeityDurg's unfinished release

- Starting with this Github repository with:
  - formal documentation applied
  - software license
  - as pip module
  - include unit tests
  - managed by GitHub workflows
- this is DeityDurg's dragonified / maintained pip module version of the script.  Changes from here will be moving forward.

- You can't install this yet as its unfinished.  Coming soon(tm)

-------------------

## Features

- Embeddings tracking database in ``embeddings.json``, running the file the first time automatically creates the database.
- Pickle scanner to detect mallicious pickle injections and log bad actors
- ClamAV virus scanner to detect mallicious malware in embedding downloads and log bad actors
- Clean, single-file implementation to allow including huggingface embeddings in your experiments

-------------------

## License

Please visit [here](./LICENSE.md) for a copy of the repository's software license. 

-------------------

## Contributing

Please visit [here](./CONTRIBUTING.md) to review contributing guidelines.