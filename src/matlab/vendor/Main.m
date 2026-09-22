%% Main File
%This File computes statistcs 


%Table 2
%Computes the statistics for the baseline economy (Table 2, Panel B)
run('climate_persistent_wf.m')
%Computes the statistics for the economy without hurricane risk (Table 2, Panel C)
run('climate_persistent_nh_wf.m')

%Table 3
%Computes the statistics for the economy with climate change (Table 3, Panel A)
run('climate_change_persistent_wf.m')
%Computes the statistics for the economy with a increase only in the frequency of hurricanes  (Table 3, Panel B)
run('climate_change_freq_persistent_wf.m')
%Computes the statistics for the economy with a increase only in the intensity of  hurricanes (Table 3, Panel C)
run('climate_change_int_persistent_wf.m')


%Table 4
%Computes the statistics for the economy with the coupon suspension clause (Table 4, Panel A)
run('climate_w_clause_persistent_wf.m')
%Computes the statistics for the economy with the coupon suspension clause and adjusted durations (Table 4, Panel B)
run('climate_w_clause_persistent_durationmod_wf.m')
%Computes the statistics for the economy with the debt reduction clause (Table 4, Panel C)
run('climate_w_clause_persistent_durationmod_wf.m')

%Table 5
%Computes the statistics for the economy with the coupon suspension clause (Table 5, Panel A)
run('climate_change_w_clause_persistent_wf.m')
%Computes the statistics for the economy with the coupon suspension clause and adjusted durations (Table 5, Panel B)
run('climate_change_w_clause_persistent_durationmod_wf.m')
%Computes the statistics for the economy with the debt reduction clause (Table 5, Panel C)
run('climate_change_w_clause_persistent_pardef_wf.m')


%Figures 1, 2, and 3
run('qfigure.m')
