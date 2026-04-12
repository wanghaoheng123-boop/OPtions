import numpy as np
import pandas as pd
import scipy.stats as si
from typing import Tuple

class GreeksCalculator:
    """
    Quantitative Analysis Agent calculation module.
    Responsible for deterministic, rigorous calculation of Black-Scholes variables and their Greeks.
    No LLM Hallucinations allowed here.

    Implements:
    - d1, d2 (Black-Scholes foundation)
    - Delta (1st order, price sensitivity)
    - Gamma (1st order, delta sensitivity to price)
    - Vega (1st order, volatility sensitivity)
    - Theta (1st order, time decay)
    - Rho (1st order, interest rate sensitivity)
    - Vanna (2nd order, delta sensitivity to volatility)
    - Charm (2nd order, delta sensitivity to time)
    """

    @staticmethod
    def _d1(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Black-Scholes d1 formula with continuous dividend yield.
        d1 = (ln(S/K) + (r - q + sigma^2/2)*T) / (sigma*sqrt(T))
        """
        if T <= 0 or sigma <= 0:
            return 0.0
        return (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    @staticmethod
    def _d2(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """d2 = d1 - sigma*sqrt(T)"""
        if T <= 0 or sigma <= 0:
            return 0.0
        return (np.log(S / K) + (r - q - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    # === FIRST-ORDER GREEKS ===

    @classmethod
    def call_price(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """Black-Scholes call price: S*e^(-qT)*N(d1) - K*e^(-rT)*N(d2)"""
        if T <= 0 or sigma <= 0:
            return max(0, S - K)
        d1 = cls._d1(S, K, T, r, sigma, q)
        d2 = cls._d2(S, K, T, r, sigma, q)
        return S * np.exp(-q * T) * si.norm.cdf(d1) - K * np.exp(-r * T) * si.norm.cdf(d2)

    @classmethod
    def put_price(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """Black-Scholes put price: K*e^(-rT)*N(-d2) - S*e^(-qT)*N(-d1)"""
        if T <= 0 or sigma <= 0:
            return max(0, K - S)
        d1 = cls._d1(S, K, T, r, sigma, q)
        d2 = cls._d2(S, K, T, r, sigma, q)
        return K * np.exp(-r * T) * si.norm.cdf(-d2) - S * np.exp(-q * T) * si.norm.cdf(-d1)

    @classmethod
    def call_delta(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Call Delta = N(d1) * e^(-qT)
        Represents the rate of change of call price with respect to underlying price.
        """
        if T <= 0 or sigma <= 0:
            return 1.0 if S > K else 0.0
        d1 = cls._d1(S, K, T, r, sigma, q)
        return np.exp(-q * T) * si.norm.cdf(d1)

    @classmethod
    def put_delta(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Put Delta = N(d1) * e^(-qT) - 1
        For puts, delta is always negative (between -1 and 0).
        """
        return cls.call_delta(S, K, T, r, sigma, q) - 1.0

    @classmethod
    def gamma(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Gamma = N'(d1) / (S * sigma * sqrt(T))
        Rate of change of Delta with respect to underlying price.
        Same for calls and puts.
        """
        if T <= 0 or sigma <= 0 or S <= 0:
            return 0.0
        d1 = cls._d1(S, K, T, r, sigma, q)
        return si.norm.pdf(d1) / (S * sigma * np.sqrt(T))

    @classmethod
    def vega(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Vega = S * N'(d1) * sqrt(T)
        Sensitivity of option price to changes in implied volatility.
        Same for calls and puts. Usually quoted per 1% change in IV.
        """
        if T <= 0 or sigma <= 0:
            return 0.0
        d1 = cls._d1(S, K, T, r, sigma, q)
        return S * si.norm.pdf(d1) * np.sqrt(T)

    @classmethod
    def theta(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0,
              option_type: str = 'call') -> float:
        """
        Theta = -S*N'(d1)*sigma/(2*sqrt(T)) - r*K*e^(-rT)*N(d2) + q*S*e^(-qT)*N(d1) [call]
        For put: add +r*K*e^(-rT)*N(-d2) - q*S*e^(-qT)*N(-d1)
        Rate of change of option price with respect to time (time decay).
        Returns daily theta (divide annual theta by 365).
        Usually quoted per 1 day, so divide by 365.
        """
        if T <= 0.0001 or sigma <= 0:
            return 0.0

        d1 = cls._d1(S, K, T, r, sigma, q)
        d2 = cls._d2(S, K, T, r, sigma, q)
        pdf_d1 = si.norm.pdf(d1)

        term1 = -S * pdf_d1 * sigma / (2 * np.sqrt(T))
        term2 = r * K * np.exp(-r * T)
        term3 = q * S * np.exp(-q * T)

        if option_type.lower() == 'call':
            theta = term1 - term2 * si.norm.cdf(d2) + term3 * si.norm.cdf(d1)
        else:  # put
            theta = term1 + term2 * si.norm.cdf(-d2) - term3 * si.norm.cdf(-d1)

        # Return daily theta (divide by 365 for per-day)
        return theta / 365.0

    @classmethod
    def rho(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0,
            option_type: str = 'call') -> float:
        """
        Rho = K*T*e^(-rT)*N(d2) [call] or -K*T*e^(-rT)*N(-d2) [put]
        Sensitivity of option price to interest rate changes.
        Usually quoted per 1% change in r (multiply by 0.01).
        """
        if T <= 0 or sigma <= 0:
            return 0.0

        d1 = cls._d1(S, K, T, r, sigma, q)
        d2 = cls._d2(S, K, T, r, sigma, q)

        if option_type.lower() == 'call':
            rho = K * T * np.exp(-r * T) * si.norm.cdf(d2)
        else:  # put
            rho = -K * T * np.exp(-r * T) * si.norm.cdf(-d2)

        # Return per 1% change in interest rate
        return rho * 0.01

    # === SECOND-ORDER GREEKS ===

    @classmethod
    def vanna(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Vanna = dDelta/dVol = N'(d1) * (d2 - d1) / (sigma * sqrt(T))
        Also = dVega/dS

        Second-order Greek: sensitivity of Delta to changes in volatility.
        Also represents the sensitivity of Vega to changes in the underlying.
        Important for delta-hedging in volatile markets.
        """
        if T <= 0.0001 or sigma <= 0 or S <= 0:
            return 0.0

        d1 = cls._d1(S, K, T, r, sigma, q)
        d2 = cls._d2(S, K, T, r, sigma, q)
        pdf_d1 = si.norm.pdf(d1)

        vanna = pdf_d1 * (d2 - d1) / (sigma * np.sqrt(T))
        return vanna

    @classmethod
    def charm(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0,
              option_type: str = 'call') -> float:
        """
        Charm = dDelta/dTime = -S*N'(d1)*sigma/(2*sqrt(T))*e^(-qT) - q*S*e^(-qT)*N(d1) [call]
        Also known as "Delta decay".

        Second-order Greek: sensitivity of Delta to time passage.
        Important for delta hedging over time — tells you how your delta hedge needs to adjust.
        """
        if T <= 0.0001 or sigma <= 0 or S <= 0:
            return 0.0

        d1 = cls._d1(S, K, T, r, sigma, q)
        d2 = cls._d2(S, K, T, r, sigma, q)
        pdf_d1 = si.norm.pdf(d1)

        term1 = -S * pdf_d1 * sigma * np.exp(-q * T) / (2 * np.sqrt(T))

        if option_type.lower() == 'call':
            term2 = q * S * np.exp(-q * T) * si.norm.cdf(d1)
            charm = term1 - term2
        else:  # put
            term2 = q * S * np.exp(-q * T) * si.norm.cdf(-d1)
            charm = term1 + term2

        # Return daily charm
        return charm / 365.0

    @classmethod
    def color(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Color = dGamma/dTime
        Third-order Greek: rate of change of Gamma with respect to time.
        Important for understanding how gamma exposure changes as expiration approaches.
        """
        if T <= 0.0001 or sigma <= 0 or S <= 0:
            return 0.0

        d1 = cls._d1(S, K, T, r, sigma, q)
        d2 = cls._d2(S, K, T, r, sigma, q)
        pdf_d1 = si.norm.pdf(d1)

        # Simplified color approximation (full formula is complex)
        color = (-pdf_d1 / (2 * S * T * sigma * np.sqrt(T))) * (
            (r - q + 0.5 * sigma ** 2) * d1 / (sigma * np.sqrt(T)) + (1 - d1 ** 2) / (2 * T)
        )
        return color / 365.0

    @classmethod
    def speed(cls, S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
        """
        Speed = d^2Gamma/dS^2 = N'(d1) * (2*gamma + 1/S + d1/(S*sigma*sqrt(T))) / (S^2 * sigma * sqrt(T))
        Third-order Greek: rate of change of Gamma with respect to underlying price.
        Used in gamma scalping strategies.
        """
        if T <= 0.0001 or sigma <= 0 or S <= 0:
            return 0.0

        d1 = cls._d1(S, K, T, r, sigma, q)
        pdf_d1 = si.norm.pdf(d1)
        gamma = cls.gamma(S, K, T, r, sigma, q)

        speed = pdf_d1 * (2 * gamma + 1/S + d1 / (S * sigma * np.sqrt(T))) / (S ** 2 * sigma * np.sqrt(T))
        return speed

    @classmethod
    def attach_greeks_to_chain(cls, df: pd.DataFrame, current_price: float,
                                risk_free_rate: float, time_to_expiry_years: float,
                                option_type: str = 'call',
                                dividend_yield: float = 0.0) -> pd.DataFrame:
        """
        Attaches calculated rigorous Greeks to an options chain DataFrame.
        Requires columns 'strike' and 'impliedVolatility'.
        """
        if df.empty or 'strike' not in df.columns or 'impliedVolatility' not in df.columns:
            return df

        df = df.copy()
        S = current_price
        r = risk_free_rate
        T = time_to_expiry_years
        q = dividend_yield

        def safe_calc_greeks(row):
            K = row['strike']
            sigma = row['impliedVolatility']

            if sigma <= 0.01:
                sigma = 0.01
            # Use a local variable to avoid shadowing outer T
            T_local = T if T > 0 else 0.0001

            try:
                delta = cls.call_delta(S, K, T_local, r, sigma, q) if option_type == 'call' else cls.put_delta(S, K, T_local, r, sigma, q)
                gamma = cls.gamma(S, K, T_local, r, sigma, q)
                vega = cls.vega(S, K, T_local, r, sigma, q)  # per 1% IV
                theta = cls.theta(S, K, T_local, r, sigma, q, option_type)
                rho = cls.rho(S, K, T_local, r, sigma, q, option_type)
                vanna = cls.vanna(S, K, T_local, r, sigma, q)
                charm = cls.charm(S, K, T_local, r, sigma, q, option_type)

                return pd.Series({
                    'calc_delta': delta,
                    'calc_gamma': gamma,
                    'calc_vega': vega,
                    'calc_theta': theta,      # daily theta in price units
                    'calc_rho': rho,          # per 1% rate change
                    'calc_vanna': vanna,
                    'calc_charm': charm
                })
            except Exception:
                return pd.Series({
                    'calc_delta': 0, 'calc_gamma': 0, 'calc_vega': 0,
                    'calc_theta': 0, 'calc_rho': 0, 'calc_vanna': 0, 'calc_charm': 0
                })

        greeks_series = df.apply(safe_calc_greeks, axis=1)
        return pd.concat([df, greeks_series], axis=1)

    @classmethod
    def calculate_greeks_for_strike(cls, S: float, K: float, T: float, r: float,
                                    sigma: float, q: float = 0.0,
                                    option_type: str = 'call') -> dict:
        """
        Calculate all Greeks for a single strike price.
        Returns a comprehensive dictionary of all Greeks.
        """
        if sigma <= 0.01:
            sigma = 0.01
        if T <= 0:
            T = 0.0001

        price = cls.call_price(S, K, T, r, sigma, q) if option_type == 'call' else cls.put_price(S, K, T, r, sigma, q)
        delta = cls.call_delta(S, K, T, r, sigma, q) if option_type == 'call' else cls.put_delta(S, K, T, r, sigma, q)
        gamma = cls.gamma(S, K, T, r, sigma, q)
        vega = cls.vega(S, K, T, r, sigma, q)
        theta = cls.theta(S, K, T, r, sigma, q, option_type)
        rho = cls.rho(S, K, T, r, sigma, q, option_type)
        vanna = cls.vanna(S, K, T, r, sigma, q)
        charm = cls.charm(S, K, T, r, sigma, q, option_type)
        color = cls.color(S, K, T, r, sigma, q)
        speed = cls.speed(S, K, T, r, sigma, q)

        return {
            "strike": K,
            "spot": S,
            "time_to_expiry": T,
            "risk_free_rate": r,
            "dividend_yield": q,
            "implied_volatility": sigma,
            "option_type": option_type,
            "price": round(price, 4),
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "vega": round(vega, 4),       # per 1% IV
            "theta": round(theta, 6),      # daily
            "rho": round(rho, 4),          # per 1% rate
            "vanna": round(vanna, 6),
            "charm": round(charm, 6),      # daily
            "color": round(color, 8),
            "speed": round(speed, 8)
        }