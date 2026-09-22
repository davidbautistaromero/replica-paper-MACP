%This file generates figure 1 and 2 in the Paper

clear all
run('climate_persistent_antiguafull.m')
clear all
run('climate_persistent_nh_antiguafull.m')
clear all
run('climate_w_clause_persistent_antiguafull.m')
clear all
run('climate_w_clause_persistent_antiguafull_pardef.m')



load 'climate_persistent_antiguafull.mat'
q_g_nofunction =q_g;
q_g_pf_nofunction =q_g_pf;
q_g_pf_nofunction = reshape(q_g_pf_nofunction,N_h,N_y,N_b_g );
[~,b_g_pf_nofunction] = max(prob_choice,[],3);
b_g_pf_nofunction = reshape(b_g_pf_nofunction,N_h,N_y,N_b_g );


clearvars -except q_g_nofunction q_g_pf_nofunction b_g_pf_nofunction def_pf_nofunction b_g_vec meanV_g_sim
load 'climate_persistent_nh_antiguafull.mat'
q_g_nh =q_g;
q_g_pf_nh =q_g_pf;
q_g_pf_nh = reshape(q_g_pf_nh,N_h,N_y,N_b_g );
[~,b_g_pf_nh] = max(prob_choice,[],3);
b_g_pf_nh = reshape(b_g_pf_nh,N_h,N_y,N_b_g );



clearvars -except b_g_vec q_g_nofunction q_g_pf_nofunction b_g_pf_nofunction def_pf_nofunction q_g_nh q_g_pf_nh b_g_pf_nh def_pf_nh
load 'climate_w_clause_persistent_antiguafull.mat'
q_g_wclause =q_g;
q_g_pf_wclause =q_g_pf;
q_g_pf_wclause = reshape(q_g_pf_wclause,N_h,N_y,N_b_g );
[~,b_g_pf_wclause] = max(prob_choice,[],3);
b_g_pf_wclause = reshape(b_g_pf_wclause,N_h,N_y,N_b_g );


clearvars -except b_g_vec q_g_nofunction q_g_pf_nofunction b_g_pf_nofunction def_pf_nofunction...
    q_g_nh q_g_pf_nh b_g_pf_nh def_pf_nh q_g_wclause q_g_pf_wclause b_g_pf_wclause
load 'climate_w_clause_persistent_antiguafull_pardef.mat'
q_g_wclause_pardef =q_g;
q_g_pf_wclause_pardef =q_g_pf;
q_g_pf_wclause_pardef = reshape(q_g_pf_wclause_pardef,N_h,N_y,N_b_g );
[~,b_g_pf_wclause_pardef] = max(prob_choice,[],3);
b_g_pf_wclause_pardef = reshape(b_g_pf_wclause_pardef,N_h,N_y,N_b_g );
%% Figure 1
close all
b_g_vec1 = b_g_vec./(delta+mu_r);
figure(1);
hFig=figure(1);
q_g_nh1=q_g_nh;
box on;
plot(b_g_vec1,q_g_nofunction(631,:),'linewidth',2,'Linestyle','-')
hold on
plot(b_g_vec1,q_g_nh1(631,:),'linewidth',2,'Linestyle',':','Color','Green')
xlab = xlabel('Debt','FontSize',15);
ylab = ylabel('q','FontSize',15);
xlim([b_g_vec1(1,20)+0.01,2.5])
legend boxoff
grid on
set(gcf, 'PaperSize', [8 4.5]); %Set the paper to have width 5 and height 5.
set(gcf, 'PaperPosition', [0 0 8 4.5]); %Position plot at left hand corner with width 5 and height 5.
legend('q: baseline','q: w/o hurricane risk','FontSize',15)
legend boxoff

print(hFig,'-dpdf','q_nh_rev.pdf','-opengl')

%% Figure 2

close all
b_g_vec1 = 100.*b_g_vec./(delta+mu_r);

figure(2);
hFig=figure(2);
box on;
plot(b_g_vec1,q_g_nofunction(101,:),'linewidth',2,'Linestyle','-')
hold on
plot(b_g_vec1,q_g_wclause(101,:),'linewidth',2,'Linestyle','--')
hold on
plot(b_g_vec1,q_g_wclause_pardef(101,:),'linewidth',2,'Linestyle','-.')
xlab = xlabel('Percentage Debt-to-GDP','FontSize',15);
ylab = ylabel('q','FontSize',15);
xlim([b_g_vec1(1,20)+1,150])
legend boxoff
grid on
set(gcf, 'PaperSize', [8 4.5]); %Set the paper to have width 5 and height 5.
set(gcf, 'PaperPosition', [0 0 8 4.5]); %Position plot at left hand corner with width 5 and height 5.
legend('q: baseline','q: coupon suspension','q: debt reduction','FontSize',15,'Location', 'Best')
legend boxoff

print(hFig,'-dpdf','q_hurr.pdf','-opengl')


%% Figure 3
close all
% y-process parameters
sigma_ey = .046; %Variance of the income shock
rho_y    = .92; %Outcorrelation parameter of income
beta     =  .915; %Discount Factor
wc_par_asymm   = .75; %Output Costs of default
delta = 0.0824; %Decay parameter
sigma_eh = .029; %Variance of the hurricane shock
mean_h    = 1-0.049; %Mean impact of hurricanes
p_hu = 0.103; %Probability of a hurricane hit



 
% clear all
gamma_c = 2;            % RRA in consumer preferences

% Intertemporal Parameters 
lambda   = 1/3;% .1;           % Dias 0.33
lambda1   = 1;% .1;           % Probability of  reentering sovereign debt contract after hurricane relief

def_cost_asymm = 1; % = 1 if default cost a la arellano, 0 if aguiar gopinath,2 Eygnour

wc_par_symm    = 0.98;%.98;          % Welfare cost of def't: Fraction of output available in default state. Not piecewise.
cost2f = 0.20;
cost1f = -0.18;
% Parameters for exogenous processses
    
% r-process parameters
mu_r    = .0451;%.001;
rho_r   = .90;%.95; % JFV =.95;


% H-process parameters
rho_u=0;


% Number of exogenous gridpoints
N_y     = 63; %50 Number of y-gridpoints
N_h     = 20; % 20 Number of h-gridpoints
N_x     = N_h*N_y; %Total number of gridpoints for exogenous process
% NUmber of endogenous gridpoints
N_b_g       = 150;%158;750;

% Number of s.d. spanned by processes. If N_variable = 1, degenerate distribution at mean
int_y       = 2.5*(N_y~=1) + eps*(N_y==1);    
int_h       = 2*(N_h~=1) + eps*(N_h==1);    


N = N_y;
mu= -.5*sigma_ey^2/(1-rho_y^2);
rho = rho_y;
sigma = sigma_ey;
m=int_y; 
Z     = zeros(N,1);
Zprob = zeros(N,N);
a     = (1-rho)*mu;

Z(N)  = m * sqrt(sigma^2 / (1 - rho^2));
Z(1)  = -Z(N);
zstep = (Z(N) - Z(1)) / (N - 1);

for i=2:(N-1)
    Z(i) = Z(1) + zstep * (i - 1);
end 

Z = Z + a / (1-rho);


ly_vec =Z;
y_vec = exp(ly_vec);

prova =b_g_pf_nofunction(1,:,38);
prova1 = prova(1,2:end);
prova1 = [prova1,NaN];
prova2 = abs(prova1-prova);
prova3 = prova;
for i=2:size(prova,2)
    if isnan(prova3(1,i-1))==0
    prova3(1,i)=prova3(1,i-1)+prova2(1,i-1);
    else
    end
end
prova3 = b_g_vec(prova3)./(delta+mu_r);
b_g_pf_wclause1 = b_g_vec(b_g_pf_wclause)./(delta+mu_r);

close all
figure(2)
subplot(1,2,1)
hFig=figure(2);
box on;
plot(y_vec,b_g_vec(b_g_pf_nofunction(1,:,65))./(delta+mu_r),'linewidth',2,'Linestyle','-')
hold on
plot(y_vec,b_g_vec(b_g_pf_wclause(1,:,65))./(delta+mu_r),'linewidth',2,'Linestyle','--')
hold on
plot(y_vec,b_g_vec(b_g_pf_wclause_pardef(1,:,65))./(delta+mu_r),'linewidth',2,'Linestyle',':')
xlab = xlabel('y','FontSize',15);
ylab = ylabel('b^{\prime}','FontSize',15);
ylim([min(b_g_vec(b_g_pf_nofunction(1,:,65))./(delta+mu_r))-0.06,max(b_g_vec(b_g_pf_wclause_pardef(1,:,65))./(delta+mu_r))+0.02])

legend boxoff
grid on
legend('Benchmark','Coupon suspension','Debt Reduction','FontSize',15,'Location','SouthEast')
legend boxoff
title('Panel A: Policy Functions for b^{\prime}')


q_g_pf_nofunction1=q_g_pf_nofunction;
q_g_pf_wclause1=q_g_pf_wclause;
q_g_pf_nofunction(isnan(q_g_pf_nofunction)==1)=0;
q_g_pf_wclause(isnan(q_g_pf_wclause)==1)=0;

subplot(1,2,2)
box on;
plot(y_vec,squeeze(q_g_pf_nofunction(2,:,65)),'linewidth',2,'Linestyle','-')
hold on
plot(y_vec,squeeze(q_g_pf_wclause(2,:,65)),'linewidth',2,'Linestyle','--')
hold on
plot(y_vec,squeeze(q_g_pf_wclause_pardef(2,:,65)),'linewidth',2,'Linestyle',':')
xlab = xlabel('y','FontSize',15);
ylab = ylabel('q','FontSize',15);
% ylim([0 7.5])
legend boxoff
grid on
set(gcf, 'PaperSize', [9 4.5]);
set(gcf, 'PaperPosition', [0 0 9 4.5]); 
legend('Benchmark','Coupon suspension','debt reduction','FontSize',15,'Location','Best')
legend boxoff
title('Panel B: Conditional Prices of Government Debt')


print(hFig,'-dpdf','policybq_rev.pdf','-opengl')
