# =============================================================================
# Chapter 3: Loads and Load Combinations (Refactored)
# - Separated Vehicle Live Loads and Footpath Live Loads into distinct tables
# - Clean tabular layout with proper Units and IRC 6 design clauses
# - Multi-page LongTable headers with \endfirsthead and \endhead
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from .styles import make_longtable


def ch3_loads(input_dict):
    # -------------------------------------------------------------------------
    # 1. Live load vehicle names mapping
    # -------------------------------------------------------------------------
    vehicles = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        vehicles.append("Class A")
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        vehicles.append("Class 70R (Wheeled)")
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        vehicles.append("Class 70R (Tracked)")
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        vehicles.append("Class AA (Wheeled)")
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        vehicles.append("Class AA (Tracked)")
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        vehicles.append("Class SV")
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        vehicles.append("Class 70R (Bogie)")
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        vehicles.append("Class Fatigue")

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get('name'):
                vehicles.append(c['name'])
            elif isinstance(c, str):
                vehicles.append(c)

    vehicles_str = ", ".join(vehicles) if vehicles else "None Specified"

    # -------------------------------------------------------------------------
    # 2. Dynamic Impact Factor calculation (IRC 6: Cl 208)
    # -------------------------------------------------------------------------
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    span = input_dict.get(KEY_SPAN)
    impact_factor_str = "N/A"
    if span not in (None, ""):
        try:
            span_m = float(span)
            factors = []
            if input_dict.get(KEY_LL_IRC_CLASS_A):
                im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
                factors.append(f"Class A: {1.0 + im_a:.3f}")
            
            is_wheeled_heavy = (
                input_dict.get(KEY_LL_IRC_70R_WHEELED) or
                input_dict.get(KEY_LL_IRC_AA_WHEELED) or
                input_dict.get(KEY_LL_IRC_70R_BOGIE)
            )
            is_tracked_heavy = (
                input_dict.get(KEY_LL_IRC_70R_TRACKED) or
                input_dict.get(KEY_LL_IRC_AA_TRACKED)
            )
            if is_wheeled_heavy or is_tracked_heavy:
                im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
                factors.append(f"Class AA/70R: {1.0 + im_aa:.3f}")

            if factors:
                impact_factor_str = ", ".join(factors)
        except Exception:
            impact_factor_str = "N/A"

    # -------------------------------------------------------------------------
    # 3. Longitudinal Braking Force (IRC 6: Cl 211)
    # -------------------------------------------------------------------------
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_str = "N/A"
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} t)"
        except Exception:
            braking_force_str = "N/A"

    # -------------------------------------------------------------------------
    # 4. Footpath Live Load Parameters (IRC 6: Cl 206)
    # -------------------------------------------------------------------------
    fp_val = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)
    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "Standard")
    if fp_val not in (None, ""):
        footpath_pressure_str = f"{float(fp_val):.2f}"
    else:
        footpath_pressure_str = "4.00 (Default)"

    # -------------------------------------------------------------------------
    # 5. Seismic Parameters (IRC 6: Cl 218)
    # -------------------------------------------------------------------------
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I — Rocky or Hard": 1, "Type II — Medium Soil": 2, "Type III — Soft Soil": 3}
            _st = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah = _res.get("Ah")
            if not sl_av:
                sl_av = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # -------------------------------------------------------------------------
    # 6. Temperature Loads (IRC 6: Cl 215)
    # -------------------------------------------------------------------------
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise = f"{_bt_max - _mean:.2f}"
            tl_fall = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # -------------------------------------------------------------------------
    # 7. Load Combinations (IRC 6: Table B.1 to B.4)
    # -------------------------------------------------------------------------
    _LOAD_LABEL_MAP = {
        'dead_load': 'DL',
        'surfacing': 'SIDL',
        'live_load': 'LL',
        'wind_load': 'WL',
        'thermal_load': 'TL',
        'vehicle_collision': 'VC',
        'barge_impact': 'BI',
        'floating_bodies': 'FB',
        'seismic': 'EQ',
    }

    def _fmt_factors(factors):
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(f"\\textbf{{ULS-{i:02d}}} & {cases} \\\\[4pt] \\hline")
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(f"\\textbf{{SLS-{i:02d}}} & {cases} \\\\[4pt] \\hline")
    lc_rows_str = "\n".join(lc_rows)

    # -------------------------------------------------------------------------
    # 8. Assemble Chapter 3 LaTeX Document
    # -------------------------------------------------------------------------
    return r"""
\chapter{Loads and Load Combinations}
This section summarizes all permanent, transient, and environmental loads applied to the bridge and the load combinations considered for structural analysis and design in accordance with IRC:6-2017.

\vspace{0.8em}
\subsection{Permanent Dead Loads (DL \& SIDL)}

\begin{longtable}{|L{6.0cm}|p{6.5cm}|C{2.5cm}|}
\caption{\textbf{Dead Load --- Structural Self Weight}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Material / Description} & \textbf{Value / Unit} \\
\hline
\endfirsthead
\multicolumn{3}{c}{\small\textit{Table continued from previous page}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Material / Description} & \textbf{Value / Unit} \\
\hline
\endhead
\hline
\multicolumn{3}{r}{\footnotesize\textit{Continued on next page\dots}} \\
\endfoot
\hline
\endlastfoot
Structural Steel Girder Density & Nominal Unit Weight & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, r' kN/m\textsuperscript{3}')) + r""" \\ \hline
Concrete Deck Slab Density & Reinforced Concrete (M35/M40) & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, r' kN/m\textsuperscript{3}')) + r""" \\ \hline
Self-Weight Application Factor & Analysis Magnification Factor & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\ \hline
\end{longtable}

\vspace{0.8em}
\begin{longtable}{|L{6.0cm}|p{6.5cm}|C{2.5cm}|}
\caption{\textbf{Superimposed Dead Load (SIDL)}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Description} & \textbf{Value / Unit} \\
\hline
\endfirsthead
\multicolumn{3}{c}{\small\textit{Table continued from previous page}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Description} & \textbf{Value / Unit} \\
\hline
\endhead
\hline
\multicolumn{3}{r}{\footnotesize\textit{Continued on next page\dots}} \\
\endfoot
\hline
\endlastfoot
Wearing Course Material & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" & """ + (_render_value(input_dict, KEY_WC_THICKNESS, ' mm')) + r""" \\ \hline
Crash Barrier SIDL & Concrete New Jersey Crash Barrier & """ + (_render_value(input_dict, KEY_CB_LOAD, ' kN/m per barrier')) + r""" \\ \hline
Railing / Parapet Load & Edge RCC Railing Load & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE, r' kN/m\sdstar{}')) + r""" \\ \hline
\end{longtable}

\vspace{1.0em}
\subsection{Live Loads (LL) --- Vehicular \& Pedestrian}

% --- TABLE 3.3: VEHICLE LIVE LOADS (Clean Distinct Table with Units) ---
\begin{longtable}{|L{4.2cm}|L{4.8cm}|C{3.2cm}|C{2.8cm}|}
\caption{\textbf{Vehicular Live Loads (IRC:6-2017)}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Vehicle Class / Description} & \textbf{Design Value} & \textbf{Unit / Standard} \\
\hline
\endfirsthead
\multicolumn{4}{c}{\small\textit{Table continued from previous page}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Vehicle Class / Description} & \textbf{Design Value} & \textbf{Unit / Standard} \\
\hline
\endhead
\hline
\multicolumn{4}{r}{\footnotesize\textit{Continued on next page\dots}} \\
\endfoot
\hline
\endlastfoot
Vehicles Considered & Selected Traffic Load Config & """ + _tex(vehicles_str) + r""" & IRC:6 Table 2 \\ \hline
Impact Factor & Dynamic Allowance Factor & """ + _tex(impact_factor_str) + r""" & IRC:6 Cl 208 \\ \hline
Braking Load & Longitudinal Braking Force & """ + _tex(braking_force_str) + r""" & IRC:6 Cl 211 \\ \hline
Centrifugal Force & Lateral Force on Curvature & 0.00 (Straight Align.) & kN (IRC:6 Cl 212) \\ \hline
\end{longtable}

\vspace{1.0em}
% --- TABLE 3.4: FOOTPATH LIVE LOAD (Separate Table as requested in Scope of Work) ---
\begin{longtable}{|L{4.5cm}|L{5.0cm}|C{2.8cm}|C{2.7cm}|}
\caption{\textbf{Pedestrian / Footpath Live Load (IRC:6-2017)}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Specification / Mode} & \textbf{Value} & \textbf{Unit / Clause} \\
\hline
\endfirsthead
\multicolumn{4}{c}{\small\textit{Table continued from previous page}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Specification / Mode} & \textbf{Value} & \textbf{Unit / Clause} \\
\hline
\endhead
\hline
\multicolumn{4}{r}{\footnotesize\textit{Continued on next page\dots}} \\
\endfoot
\hline
\endlastfoot
Footpath Provision & Pedestrian Footway Setup & """ + _tex(str(input_dict.get('footpath', 'None'))) + r""" & UI Input \\ \hline
Footpath Pressure Mode & Pressure Distribution Type & """ + _tex(str(fp_mode)) + r""" & User / Default \\ \hline
Design Live Pressure & Footpath Crowd Loading Intensity & """ + _tex(footpath_pressure_str) + r""" & kN/m\textsuperscript{2} (IRC:6 Cl 206) \\ \hline
\end{longtable}

\vspace{1.0em}
\subsection{Environmental Loads (Wind, Seismic \& Temperature)}

\begin{longtable}{|L{5.5cm}|p{6.8cm}|C{2.7cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC:6-2017}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Description} & \textbf{Value / Unit} \\
\hline
\endfirsthead
\multicolumn{3}{c}{\small\textit{Table continued from previous page}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Description} & \textbf{Value / Unit} \\
\hline
\endhead
\hline
\multicolumn{3}{r}{\footnotesize\textit{Continued on next page\dots}} \\
\endfoot
\hline
\endlastfoot
Basic Wind Speed, Vb & Regional Wind Zone & """ + (_render_value(input_dict, 'wind_speed', ' m/s')) + r""" \\ \hline
Terrain Category & Aerodynamic Terrain Exposure & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\ \hline
Average Exposed Height & Superstructure Height H & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\ \hline
Hourly Mean Wind, Vz & Design Wind Speed at Height H & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')) + r""" \\ \hline
Hourly Wind Pressure, Pz & Dynamic Transverse Pressure & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, r' N/m\textsuperscript{2}')) + r""" \\ \hline
Transverse Wind Force & Lateral Wind Force per Span & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')) + r""" \\ \hline
Longitudinal Wind Force & Along-span Wind Component & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')) + r""" \\ \hline
Vertical Wind Force & Uplift / Downward Wind Action & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')) + r""" \\ \hline
\end{longtable}

\vspace{0.8em}
\begin{longtable}{|L{5.5cm}|p{6.8cm}|C{2.7cm}|}
\caption{\textbf{Earthquake / Seismic Load (EL) --- per IRC:6-2017}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Description} & \textbf{Value / Unit} \\
\hline
\endfirsthead
\multicolumn{3}{c}{\small\textit{Table continued from previous page}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Description} & \textbf{Value / Unit} \\
\hline
\endhead
\hline
\multicolumn{3}{r}{\footnotesize\textit{Continued on next page\dots}} \\
\endfoot
\hline
\endlastfoot
Seismic Zone & Geographic Hazard Zone & """ + (_render_value(input_dict, 'seismic_zone')) + r""" \\ \hline
Zone Factor (Z) & Peak Ground Acceleration Coeff. & """ + _sl(sl_zone_factor) + r""" \\ \hline
Importance Factor (I) & Bridge Criticality Class & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\ \hline
Soil Profile Type & Foundation Soil Classification & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\ \hline
Spectral Acceleration (Sa/g) & Normalized Elastic Response & """ + _sl(sl_spectral) + r""" \\ \hline
Horizontal Coeff. (Ah) & Design Base Shear Coefficient & """ + _sl(sl_ah) + r""" \\ \hline
Vertical Coeff. (Av) & Vertical Response Coefficient & """ + _sl(sl_av) + r""" \\ \hline
\end{longtable}

\vspace{0.8em}
\begin{longtable}{|L{5.5cm}|p{6.8cm}|C{2.7cm}|}
\caption{\textbf{Thermal Actions (TL) --- per IRC:6-2017}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Description} & \textbf{Value / Unit} \\
\hline
\endfirsthead
\multicolumn{3}{c}{\small\textit{Table continued from previous page}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Parameter} & \textbf{Description} & \textbf{Value / Unit} \\
\hline
\endhead
\hline
\multicolumn{3}{r}{\footnotesize\textit{Continued on next page\dots}} \\
\endfoot
\hline
\endlastfoot
Maximum Shade Temperature & Regional Peak Air Temp & """ + (_render_value(input_dict, 'shade_temp_max')) + r""" $^\circ$C \\ \hline
Minimum Shade Temperature & Regional Lowest Air Temp & """ + (_render_value(input_dict, 'shade_temp_min')) + r""" $^\circ$C \\ \hline
Effective Bridge Temp. Range & Bridge Operating Range & """ + tl_temp_min + r""" to """ + tl_temp_max + r""" $^\circ$C \\ \hline
Temperature Rise for Design & Positive Thermal Expansion & """ + tl_rise + r""" $^\circ$C \\ \hline
Temperature Fall for Design & Negative Thermal Contraction & """ + tl_fall + r""" $^\circ$C \\ \hline
\end{longtable}

\vspace{1.0em}
\subsection{Design Load Combinations (ULS \& SLS)}

% --- MULTI-PAGE LOAD COMBINATIONS TABLE WITH AUTOMATIC REPEATED HEADERS ---
\begin{longtable}{|C{3.0cm}|p{12.0cm}|}
\caption{\textbf{Design Load Combinations (IRC:6 Table B.1 -- B.4)}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Combination ID} & \textbf{Factored Load Cases (ULS / SLS)} \\
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Table continued from previous page}} \\
\hline
\rowcolor{TableHeadBg}
\textbf{Combination ID} & \textbf{Factored Load Cases (ULS / SLS)} \\
\hline
\endhead
\hline
\multicolumn{2}{r}{\footnotesize\textit{Continued on next page\dots}} \\
\endfoot
\hline
\endlastfoot
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{\footnotesize Note: All load combinations are auto-generated in strict compliance with IRC:6-2017 (Limit State Design), covering Ultimate Limit State (ULS) and Serviceability Limit State (SLS).}
"""


