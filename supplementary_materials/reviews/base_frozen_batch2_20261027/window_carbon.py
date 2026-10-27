"""Read-only carbon accounting for an explicitly selected Base dispatch window.

Gross thermal generation is GW at one-hour steps; factors are Mt/GWh. DAC in
this model is a constant annual throughput rate, so its selected-window mass
is annual captured mass times hours/8760, consistent with monolithic.py.
"""
import numpy as np
from cispo_model.carbon_accounting import resolve_beccs_carbon_factors


def account_window(gross, technologies, hour_index, selected_hours, emissions, dac_annual):
    hours=np.asarray(hour_index)
    chosen=np.asarray(selected_hours)
    gross=np.asarray(gross,dtype=float)
    if gross.ndim!=3 or gross.shape[1]!=len(technologies) or gross.shape[2]!=8760:
        raise ValueError('Expected province/technology/8760 gross generation')
    if not np.array_equal(hours,np.arange(8760)) or not np.array_equal(chosen,np.arange(24)):
        raise ValueError('Only exact first 24 hours of verified full-year archive supported')
    if not np.isfinite(gross).all() or not np.isfinite(dac_annual) or dac_annual<0:
        raise ValueError('Nonfinite generation or invalid annual DAC mass')
    coal=float(emissions.loc['coal','emission_factor_mtco2_per_gwh'])
    gas=float(emissions.loc['gas','emission_factor_mtco2_per_gwh'])
    capture=float(emissions.loc['coal','ccs_capture_fraction'])
    beccs=resolve_beccs_carbon_factors(emissions)
    factors=[]
    for technology in technologies:
        base=coal if technology.startswith(('coal','cchp')) else gas if technology.startswith(('gas','gchp')) else 0.
        factors.append(beccs.net_emissions if technology=='bioccs' else base*(1-capture) if technology.endswith('ccs') else base)
    factors=np.asarray(factors)
    hourly=(gross.sum(axis=0)*factors[:,None]).sum(axis=0)-dac_annual/8760
    net=float(hourly[chosen].sum())
    return dict(hour_indices=chosen.tolist(),thermal_technologies=list(technologies),
        emission_factors_mt_per_gwh=factors.tolist(),hourly_net_emissions_mt=hourly[chosen].tolist(),
        thermal_gross_window_gwh=gross[:,:,chosen].sum(axis=(0,2)).tolist(),
        annual_reconstructed_net_emissions_mt=float(hourly.sum()),
        base_window_net_emissions_mt=net,window_dac_removed_mt=dac_annual*len(chosen)/8760,
        window_carbon_limit_mt=net*(1+1e-4),margin_multiplier=1.0001,
        dac_window_method='Constant annual throughput rate, as in model; annual mass * 24/8760',
        production_annual_carbon_limit_unchanged=True)
