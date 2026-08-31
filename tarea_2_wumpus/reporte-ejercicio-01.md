# Reporte — Ejercicio 1: mi cueva 4x4

La nueva cueva mantiene la cuadrícula de 4x4 y el agente inicia en la casilla
`[1,1]`, mirando al este. El Wumpus se colocó en `[4,4]`; los pits se ubicaron
en `[4,1]`, `[4,3]` y `[2,4]`; y el oro está en `[2,2]`. Estas posiciones son
distintas de las del mapa clásico y no presentan solapamientos. Existe un camino
seguro de ida y vuelta entre la salida y el oro: `[1,1] → [2,1] → [2,2]` y el
mismo trayecto en sentido inverso.

## Resultados de los agentes


| Agente                                   | Resultado         | Pasos | Puntaje |
| ---------------------------------------- | ----------------- | ----- | ------- |
| Reflejo simple                           | Se detuvo sin oro | 200   | -200    |
| Basado en modelo                         | Salió con el oro  | 11    | 989     |
| Basado en metas                          | Salió con el oro  | 11    | 989     |
| Basado en utilidad                       | Salió con el oro  | 13    | 987     |
| Aprendizaje (Q-learning, 1500 episodios) | Salió con el oro  | 10    | 990     |


Los agentes basado en modelo, basado en metas y basado en utilidad lograron
recoger el oro, regresar a la casilla inicial y salir con puntaje positivo. El
agente de reflejo simple no logró salir con el oro y agotó el límite de 200
pasos. Después de entrenarse durante 1500 episodios, el agente de aprendizaje
también salió con el oro: completó la demostración en 10 pasos y obtuvo 990
puntos.

## Resultado del agente de aprendizaje

El entrenamiento por Q-learning obtuvo un puntaje promedio de `824.7` en los
1500 episodios y de `904.5` en los últimos 50. La tabla Q terminó con 570 pares
estado-acción. En la demostración final, ya sin exploración (`epsilon = 0`), el
agente avanzó a `[2,1]`, subió a `[2,2]`, tomó el oro, regresó a `[1,1]` y usó
`Climb`. El resultado confirma que aprendió una política segura y eficaz para
esta configuración.

## ¿Por qué falla el agente de reflejo simple?

Este agente únicamente responde a la percepción de la casilla actual. No
recuerda su posición, orientación, casillas visitadas ni el camino hacia la
salida. En este diseño avanza por la fila inferior hasta percibir la brisa
producida por el pit de `[4,1]`. Después reacciona mediante giros, pero no crea
un mapa ni un plan para alcanzar el oro en `[2,2]`. Sus reglas tampoco incluyen
la acción `Climb`, de modo que no puede completar correctamente la salida aunque
regrese por casualidad a `[1,1]`.



