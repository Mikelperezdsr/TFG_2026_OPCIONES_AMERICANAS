"""
Aproximación analítica de Barone-Adesi y Whaley (1987) para opciones americanas.

El método descompone el precio de la opción americana como la suma del precio
europeo de Black-Scholes más una prima de ejercicio anticipado, obtenida de
forma aproximada al resolver una ecuación cuadrática asociada a la EDP de
Black-Scholes. La implementación asume las hipótesis estándar del modelo
(volatilidad y tipo de interés constantes) y se restringe al caso sin
dividendos (q = 0, por lo que el coste de financiación b coincide con r).

Bajo esta hipótesis no es óptimo ejercer de forma anticipada una call
americana, de modo que su precio coincide con el europeo. La prima de
ejercicio anticipado se calcula únicamente en el caso put.

Referencia: Barone-Adesi, G. y Whaley, R. E. (1987), "Efficient analytic
approximation of American option values", Journal of Finance, 42(2).
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

from utils.black_scholes import precio_bs_europeo


def precio_baw(S0, K, T, r, sigma, tipo='put'):
    """
    Precio de una opción americana mediante la aproximación de
    Barone-Adesi-Whaley (1987), sin reparto de dividendos.

    Parámetros
    ----------
    S0    : float - Precio actual del subyacente
    K     : float - Precio de ejercicio
    T     : float - Tiempo al vencimiento (años)
    r     : float - Tasa libre de riesgo
    sigma : float - Volatilidad
    tipo  : str   - 'call' o 'put'

    Retorna
    -------
    precio : float - Valor de la opción americana
    """
    # Sin dividendos no es óptimo ejercer una call antes del vencimiento:
    # el precio americano coincide con el europeo de Black-Scholes.
    if tipo == 'call':
        return precio_bs_europeo(S0, K, T, r, sigma, 'call')

    # Coeficientes auxiliares de la aproximación cuadrática (caso q = 0, b = r).
    N_param = 2 * r / sigma**2
    M_param = 2 * r / sigma**2
    K_factor = 1 - np.exp(-r * T)
    q1 = (-(N_param - 1) - np.sqrt((N_param - 1)**2 + 4 * M_param / K_factor)) / 2

    def _d1(S):
        return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))

    def _ecuacion_critica(S):
        # Condición de empalme entre la zona de continuación y la de ejercicio.
        p_eur_s = precio_bs_europeo(S, K, T, r, sigma, 'put')
        return K - S - p_eur_s + (1 - norm.cdf(-_d1(S))) * S / q1

    # Búsqueda del precio crítico S** en el intervalo (0.01*K, K). Si el
    # método numérico no converge, se devuelve el precio europeo como
    # cota inferior segura.
    try:
        S_star = brentq(_ecuacion_critica, 0.01 * K, K)
    except (ValueError, RuntimeError):
        return precio_bs_europeo(S0, K, T, r, sigma, 'put')

    A1 = -(S_star / q1) * (1 - norm.cdf(-_d1(S_star)))

    # Por debajo del precio crítico es óptimo el ejercicio inmediato.
    if S0 <= S_star:
        return K - S0

    # Por encima, se añade la prima de ejercicio anticipado al precio europeo.
    p_eur = precio_bs_europeo(S0, K, T, r, sigma, 'put')
    return p_eur + A1 * (S0 / S_star)**q1
