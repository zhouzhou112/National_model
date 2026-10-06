"""Independent original-unit LP comparison, eliminating C's auxiliary rows."""
from pathlib import Path
import argparse
import json
import sys
import numpy as np
from scipy import sparse

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from cispo_model.physical_lp_diff import compare_physical_lp_arrays


def arrays(root):return dict(np.load(root/'lp_arrays.npz')),sparse.load_npz(root/'matrix.npz').tocsr()


def audited_capacity_closures(reference, candidate, audit):
    """Allow only the independently recorded builder cleanup sites and values."""
    names={str(name):i for i,name in enumerate(reference['variable_names'])}
    closures={}
    def add(name, removed, cutoff):
        if name in closures or name not in names:
            raise ValueError('Duplicate/missing audited capacity variable: '+name)
        i=names[name];old=float(reference['upper'][i]);new=float(candidate['upper'][i])
        if not (0 < removed <= cutoff <= 1e-4 and old-new==removed
                and new==float(reference['lower'][i])):
            raise ValueError('Builder cleanup amount disagrees with bounds: '+name)
        closures[name]={'original_upper_gw':old,'closed_upper_gw':new,'maximum_removed_gw':cutoff}
    hydro=audit.get('hydro_capacity_headroom_cleanup')
    if hydro:
        if len(hydro['site_rows'])!=len(hydro['removed_gw']):raise ValueError('Hydro audit length mismatch')
        for row,removed in zip(hydro['site_rows'],hydro['removed_gw']):
            for family in ['hydro_capacity_gw','hydro_new_gw']:
                add(f'{family}[{row}]',float(removed),float(hydro['cutoff_gw']))
    for pair,record in enumerate(audit.get('retrofit_upper_cleanup',[])):
        if len(record['site_rows'])!=len(record['removed_gw']):raise ValueError('Retrofit audit length mismatch')
        for row,removed in zip(record['site_rows'],record['removed_gw']):
            if not float(removed)<float(record['cutoff_gw']):raise ValueError('Retrofit requires strict cutoff')
            add(f'thermal_retrofit_to_ccs_gw[{row},{pair}]',float(removed),float(record['cutoff_gw']))
    return closures


def compare(reference,candidate):
    ref,ar=arrays(reference);cand,ac=arrays(candidate)
    projected=0
    if any(str(n).startswith('annual_block_') for n in cand['variable_names']):
        cols=np.array([str(n).startswith('annual_block_') for n in cand['variable_names']])
        rows=np.array([str(n).startswith('annual_block_') for n in cand['row_names']])
        diagonal=ac[rows,:][:,cols].tocsr()
        assert diagonal.shape[0]==diagonal.shape[1] and (diagonal-sparse.eye(diagonal.shape[0])).nnz==0
        assert np.all(cand['senses'][rows]=='=') and np.all(cand['objective'][cols]==0)
        assert np.all(cand['upper'][cols]>=1e100), 'Auxiliary UB would change feasible projection'
        definitions=-ac[rows,:][:,~cols].tocsr()
        for j,lb in enumerate(cand['lower'][cols]):
            if lb<=-1e100:continue
            assert lb==0, 'Only free or proven redundant zero LB is allowed'
            row=definitions.getrow(j);values=row.data;indices=row.indices
            extremum=np.where(values>=0,cand['lower'][~cols][indices],cand['upper'][~cols][indices])
            minimum=float(cand['rhs'][rows][j]+values@extremum)
            assert minimum>=0, 'Auxiliary nonnegative bound is not implied by original bounds'
        # D: z + D_x x = d. Substitute into retained rows: A_x-A_z D_x, rhs-A_z d.
        az=ac[~rows,:][:,cols]
        ac=ac[~rows,:][:,~cols]-az@ac[rows,:][:,~cols]
        cand['rhs']=cand['rhs'][~rows]-az@cand['rhs'][rows]
        for key in ['senses','row_names']:cand[key]=cand[key][~rows]
        for key in ['lower','upper','objective','variable_names']:cand[key]=cand[key][~cols]
        projected=int(cols.sum())
    lookup={n:i for i,n in enumerate(cand['row_names'])};rorder=[lookup[n] for n in ref['row_names']]
    lookup={n:i for i,n in enumerate(cand['variable_names'])};corder=[lookup[n] for n in ref['variable_names']]
    assert len(rorder)==len(cand['row_names']) and len(corder)==len(cand['variable_names'])
    ac=ac[rorder,:][:,corder]
    for key in ['rhs','senses','row_names']:cand[key]=cand[key][rorder]
    for key in ['lower','upper','objective','variable_names']:cand[key]=cand[key][corder]
    build=json.loads((candidate/'build_report.json').read_text())
    closures=audited_capacity_closures(ref,cand,build.get('numerical_robustness_audit') or {})
    kwargs={f'{side}_{field}':payload[key] for side,payload in [('reference',ref),('candidate',cand)] for field,key in
        [('rhs','rhs'),('lower','lower'),('upper','upper'),('objective','objective'),('senses','senses')]}
    result=compare_physical_lp_arrays(reference_matrix=ar,candidate_matrix=ac,
        row_names=ref['row_names'],variable_names=ref['variable_names'],whitelist={'capacity_interval_closures':closures},**kwargs)
    result['auxiliary_variables_eliminated']=projected
    result['explicit_capacity_interval_whitelist']=closures
    delta=ac-ar
    result['maximum_matrix_difference']=float(abs(delta.data).max(initial=0))
    result['maximum_rhs_difference']=float(abs(ref['rhs']-cand['rhs']).max(initial=0))
    for root,name in [(reference,'reference'),(candidate,'candidate')]:
        if (root/'result.json').exists():result[name+'_solve']=json.loads((root/'result.json').read_text())
    if 'reference_solve' in result and 'candidate_solve' in result:
        a=result['reference_solve']['objective'];b=result['candidate_solve']['objective']
        result['relative_objective_difference']=None if a is None or b is None else abs(a-b)/max(1,abs(a),abs(b))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('reference',type=Path);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=compare(a.reference,a.candidate);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['status'],result['changed_upper_bounds'],result['maximum_matrix_difference'],result['maximum_rhs_difference'])
