# Psychrometrics Note

Humidity ratio proxy:

\[
\omega = 0.622 \cdot \frac{P_v}{P - P_v}
\]

with `P_v` from a Magnus-Tetens saturation-pressure approximation and a numeric guard
`P_v <= 0.99 P` for stability in extreme states.
