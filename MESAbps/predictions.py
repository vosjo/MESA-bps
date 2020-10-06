import os
import pandas as pd

from nnaps import predictors

stability_model = predictors.FCPredictor(saved_model=os.path.join('MESAbps', 'models', 'model_stability.h5'))
stable_model = predictors.FCPredictor(saved_model=os.path.join('MESAbps', 'models', 'model_stable_systems.h5'))
ce_model = predictors.FCPredictor(saved_model=os.path.join('MESAbps', 'models', 'model_ce_systems.h5'))

NECESSARY_PARAMETERS = ['M1_init', 'q_init', 'P_init', 'FeH_init']

def correct_input_pars(df):

    for parname in NECESSARY_PARAMETERS:
        if not parname in df.columns:
            return False
        
    return True


def predict(dataframe, stability_limit=-2, alpha_ce=0.3):

    df = dataframe.copy()

    # check if stability limit and alpha_ce are in the dataframe, use defaults otherwise
    if 'stability_limit' not in df.columns:
        df['stability_limit'] = stability_limit
    if 'alpha_ce' not in df.columns:
        df['alpha_ce'] = alpha_ce

    # prepare the result DF
    results = dataframe.copy()
    results['stability'] = 'merger'
    results['P_final'] = 0
    results['q_final'] = 0
    results['M1_final'] = 0
    results['M2_final'] = 0
    results['product'] = 'merger'

    # start with predicting the properties at the end of ML and the stability
    #mlend = mlend_model.predict(df)
    stability = stability_model.predict(df)
    results.loc[:,'stability'] = stability
    
    # differentiate between stable and CE systems
    ind_stable = df[stability['stability'] == 'stable'].index
    ind_ce = df[stability['stability'] == 'CE'].index
    ind_merger = df[stability['stability'] == 'merger'].index
    
    # make predictions for stable systems
    if len(ind_stable) > 0:
        stable_results = stable_model.predict(df.loc[ind_stable])
        results.loc[ind_stable, stable_results.columns.values] = stable_results.values
    
    # make predictions for CE systems
    if len(ind_ce) > 0:
        ce_results = ce_model.predict(df.loc[ind_ce])
        results.loc[ind_ce, ce_results.columns.values] = ce_results.values
    
    # mergers are ignored as they are not predictable
    
    return results
