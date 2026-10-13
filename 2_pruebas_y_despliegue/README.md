# Tema 2 — Pruebas y despliegue

## **Leyenda utilizada en la wiki**

`->` Inicio, objetivo o tarea planteada.

`~>` Desarrollo, cambio o ajuste realizado.

`>` Paso técnico llevado a cabo.

`>>` Evidencia, archivo o comprobación del paso.

`=>` Resultado obtenido o estado final de la fecha.

`->` Organizar el material y las prácticas del Tema 2.

| Sesión | Material | Ejercicio |
| --- | --- | --- |
| **28 sep** | [pytest](01_pytest_intro.md), [CI](02_ci_github.md), [ejemplos](ejemplos/) | [E3 — pytest](ejercicios/E3_pytest.md), [E4 — CI](ejercicios/E4_ci_github.md) |

`>>` CI del repo: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).


`>` Ejecutar los tests de ejemplo desde la raíz:

```bash
python -m pytest -q 2_pruebas_y_despliegue/ejemplos/test_calculator.py
```

`>>` Los tests y la cobertura del [Proyecto I](../proyectos/proyecto_i/README.md) se ejecutan con el workflow común del repositorio.
