The `fincore.py` in the root of the repository is a Python financial library. I wish to translate the Python library to a Rust crate. Since you cannot translate the entire file in a single pass, I will suggest you do it top to bottom, one Vim fold per time. The folds are marked using the Vim fold marker method, with {{{ to open a fold and }}} to close it. I will oversee the process, and for my better understanding it is important that the file translation is done as linearly as possible. Avoid leaving gaps, or any kind of placeholder code. Avoid going going back and forth in the implementations.

A `rust` subdirectory should be created. The Rust library should be generated in it, with the name `rust/fincore.rs`, alongside the `rust/Cargo.toml` file, so I can build it. Do not create the standard `src` subdirectory with a `lib.rs` file in it. Start by creating the directory structure and the required files.

The `rust/fincore.rs` should be an accurate translation of `fincore.py` into Rust.

Also note:

• To build the library from the root directory, use the `--manifest-path=rust/Cargo.toml` command line option: `cargo build --manifest-path=rust/Cargo.toml`. But do not attempt to build the library until you have finished with the translation. Also, make explanations as short as possible to save on input context size.

• Inline and static code, like `InMemoryBackend._ignore_cdi` and `InMemoryBackend._registry_cdi`, should be translated verbatim.

• Do not translate any code that deals with IPCA, Brazilian's main price level index; or IGPM, another price level index; or Poupança, Brazilian savings accounts benchmark. This means you should not translate classes `PriceLevelAdjustment`, `PriceAdjustedPayment`, `LatePriceAdjustedPayment`, and anything else relating to them. I want the code to support only prefixed loans, and CDI – Certificado de Depósito Interbancário – indexed ones.
