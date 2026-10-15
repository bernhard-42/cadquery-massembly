# Changelog

## 1.1.0 (2026-10-15)

### Added

- Support for CadQuery on nanocct in addition to OCP: the geometry helpers (`Circle`, `Line`, intersections) now take their OCCT classes from the binding CadQuery runs on, so the curves they build are always of the same kind as CadQuery's own objects.

## 1.0.0 (2022-10-23)

- Final release of 1.0.0rc1 without code changes.

## 1.0.0rc1 (2022-07-23)

### Added

- Degrees of freedom for `assemble`, with single DOF (including rotation around z) and double DOF cases.
- Circle and line intersection code to solve the DOF cases.
- `MAssembly.from_assembly` to create a MAssembly from a CadQuery assembly.
- Copying of mates.

### Changed

- Relocation is now a method of `MAssembly`.
- Prettier `repr` and dump output.
- License changed to BSD 3-Clause.

## 0.9.0 (2021-05-15)

- First tagged release.
