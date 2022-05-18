# CETONI SiLA 2 Controller SDK
## Installation
Run `pip install .` from the root directory containing the file `setup.py`

## Usage
Run `python -m sila_cetoni_controllers --help` to receive a full list of available options

## Code generation
- generate
  ```console
  $ python -m sila2.code_generator new-package -n control_loop_service -o ./sila_cetoni/controllers/sila/ ./sila_cetoni/controllers/featuresControlLoopService.sila.xml
  ```
- update
  ```console
  $ python -m sila2.code_generator update -d ./sila_cetoni/controllers/sila/ ./sila_cetoni/controllers/featuresControlLoopService.sila.xml
  ```
