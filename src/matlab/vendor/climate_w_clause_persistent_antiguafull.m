share_counter=1;
for share = 0.0
    
    for counter= 1:1
 %%
        cc_freq = 1;
        cc_int = 1;
        
if counter==1 %Antigua
% y-process parameters
sigma_ey = .046;%.006;         % Standard deviation of innovation of y. Arellano = 0.025
rho_y    = .92;%.98;          % AR coefficient for y. Arellano = 0.945
beta     =  .915;% .9;          % Subjective discount factor (Cuadra, Sanchez, Sapriza = .97) Arellano: .953
wc_par_asymm   = .75;%.8;
delta = 0.0824;% (8.2 years maturity)
sigma_eh = .029;%.006;         % Standard deviation of hurricane
mean_h    = 1-cc_int.*0.049;%.98;          % Average GDP loss with hurricane hit
p_hu = cc_freq.*0.103; %You are hit by a hurricane once every 14.8 years

elseif counter==2 %Belize
% y-process parameters
sigma_ey = .036;%.006;         % Standard deviation of innovation of y. Arellano = 0.025
rho_y    = .99;%.98;          % AR coefficient for y. Arellano = 0.945
beta     =  .945;% .97;          % Subjective discount factor (Cuadra, Sanchez, Sapriza = .97) Arellano: .953
wc_par_asymm   = 0.54;%.97;
delta = 0.0442;
sigma_eh = .028;%.006;         % Standard deviation of hurricane
mean_h    = 1-cc_int.*0.021;%.98;          % Average GDP loss with hurricane hit
p_hu = cc_freq.*0.077; %You are hit by a hurricane once every 14.8 years

elseif counter==3 %Dominica
% y-process parameters
sigma_ey = .027;%.006;         % Standard deviation of innovation of y. Arellano = 0.025
rho_y    = .94;%.98;          % AR coefficient for y. Arellano = 0.945
beta     =  .9375;% .97;          % Subjective discount factor (Cuadra, Sanchez, Sapriza = .97) Arellano: .953
wc_par_asymm   = 0.68;%.97;
delta = 0.0467;
sigma_eh = .028;%.006;         % Standard deviation of hurricane
mean_h    = 1-cc_int.*0.098;%.98;          % Average GDP loss with hurricane hit
p_hu = cc_freq.*0.026; %You are hit by a hurricane once every 21.14 years

elseif counter==4 %Dominican Republic
% y-process parameters
sigma_ey = .0464;%.006;         % Standard deviation of innovation of y. Arellano = 0.025
rho_y    = .88;%.98;          % AR coefficient for y. Arellano = 0.945
beta     =  .895;% .97;          % Subjective discount factor (Cuadra, Sanchez, Sapriza = .97) Arellano: .953
wc_par_asymm   = 0.8175;%.97;
delta = 0.1731;% 
sigma_eh = .034;%.006;         % Standard deviation of hurricane
mean_h    = 1-cc_int.*0.04;%.98;          % Average GDP loss with hurricane hit
p_hu = cc_freq.*0.051; %You are hit by a hurricane once every 24.66 years

elseif counter==5 %Grenada
% y-process parameters
sigma_ey = .052;%.006;         % Standard deviation of innovation of y. Arellano = 0.025
rho_y    = .91;%.98;          % AR coefficient for y. Arellano = 0.945
beta     =  .91;% .97;          % Subjective discount factor (Cuadra, Sanchez, Sapriza = .97) Arellano: .953
wc_par_asymm   = 0.697;%.97;
delta = 0.0612;%
sigma_eh = .052;%.006;         % Standard deviation of hurricane
mean_h    = 1-cc_int.*0.070;%.98;          % Average GDP loss with hurricane hit
p_hu = cc_freq.*0.051; %You are hit by a hurricane once every 14.8 years

elseif counter==6 %Honduras
% y-process parameters
sigma_ey = .026;%.006;         % Standard deviation of innovation of y. Arellano = 0.025
rho_y    = .83;%.98;          % AR coefficient for y. Arellano = 0.945
beta     =  .8575;% .97;          % Subjective discount factor (Cuadra, Sanchez, Sapriza = .97) Arellano: .953
wc_par_asymm   = 0.82;%.97;
delta = 0.1639;%
sigma_eh = .027;%.006;         % Standard deviation of hurricane
mean_h    = 1-cc_int.*0.052;%.98;          % Average GDP loss with hurricane hit
p_hu = cc_freq.*0.051; %You are hit by a hurricane once every 14.8 years

elseif counter==7 %Jamaica
% y-process parameters
sigma_ey = .026;%.006;         % Standard deviation of innovation of y. Arellano = 0.025
rho_y    = .96;%.98;          % AR coefficient for y. Arellano = 0.945
beta     =  .93;% .97;          % Subjective discount factor (Cuadra, Sanchez, Sapriza = .97) Arellano: .953
wc_par_asymm   = 0.73;%.97;
delta = 0.0564;% (8.2 years maturity)
sigma_eh = .02;%.006;         % Standard deviation of hurricane
mean_h    = 1-cc_int.*0.023;%.98;          % Average GDP loss with hurricane hit
p_hu = cc_freq.*0.103; %You are hit by a hurricane once every 14.8 years

end


 
% clear all
gamma_c = 2;            % RRA in consumer preferences
% gamma_l = -6.545;         % Frisch Elasticity (inverse)

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

% Generate exogenous processes 
% Process for y
%%


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

for j = 1:N
    for k = 1:N
        if k == 1
            Zprob(j,k) = 0.5 * erfc(-((Z(1) - a - rho * Z(j) + zstep / 2) / sigma)/sqrt(2));
        elseif k == N
            Zprob(j,k) = 1 - 0.5 * erfc(-((Z(N) - a - rho * Z(j) - zstep / 2) / sigma)/sqrt(2));
        else
            Zprob(j,k) = 0.5 * erfc(-((Z(k) - a - rho * Z(j) + zstep / 2) / sigma)/sqrt(2)) - ...
                         0.5 * erfc(-((Z(k) - a - rho * Z(j) - zstep / 2) / sigma)/sqrt(2));
        end
    end
end

ly_vec =Z;
P_y = Zprob;


    
%%
% Process for h
if N_h>1
% Discretize shock H
N = N_h-1;
mu= -.5*sigma_eh^2;
rho = 0;
sigma = sigma_eh;
m=int_h; 
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

for j = 1:N
    for k = 1:N
        if k == 1
            Zprob(j,k) = 0.5 * erfc(-((Z(1) - a - rho * Z(j) + zstep / 2) / sigma)/sqrt(2));
        elseif k == N
            Zprob(j,k) = 1 - 0.5 * erfc(-((Z(N) - a - rho * Z(j) - zstep / 2) / sigma)/sqrt(2));
        else
            Zprob(j,k) = 0.5 * erfc(-((Z(k) - a - rho * Z(j) + zstep / 2) / sigma)/sqrt(2)) - ...
                         0.5 * erfc(-((Z(k) - a - rho * Z(j) - zstep / 2) / sigma)/sqrt(2));
        end
    end
end

lh_vec =Z;
P_h = Zprob;


P_h = p_hu.*P_h; % I adjust the probability for the risk that I am hit by a hurricane
P_h=[(1-p_hu)*ones(N_h-1,1) , P_h];
P_h=[P_h(1,:) ; P_h];
else
lh_vec = 1;
P_h=1; 
end



%% Now put together the P_x 

y_vec = exp(ly_vec);
h_vec = mean_h*exp(lh_vec);
h_vec = [1;h_vec]; % Add the case in which there is no hurricane

h_vec_gdp = kron(ones(N_y,1),h_vec);

y_vec_gdp = kron(y_vec,ones(N_h,1));

gdp_vec = h_vec_gdp.*y_vec_gdp;

P_x_int = zeros(N_x,N_y);
for bibi=1:size(gdp_vec,1)
    prova = gdp_vec(bibi,1);
    prova2 = (prova-y_vec).^2;
    [~,index] = min(prova2);
    index_store(bibi,1)=index;
    P_x_int(bibi,:)=P_y(index,:);  
end


P_x = kron(P_x_int,ones(1,N_h));
P_h_int=kron(ones(N_y,N_y),P_h); 
P_x = P_h_int.*P_x;


r_vec =  mu_r;
r_vec_2sh = r_vec(:);


load('gdp_mean_storemat')
gdp_mean = gdp_mean_store(counter,1);



%%
P2_x=zeros(size(P_x,1),size(P_x,2));
%Compute the transition matrix two-periods ahead
for j=1:size(P_x,1)
    for i=1:size(P_x,2)
        prova1 = P_x(j,:);
        prova2 = P_x(:,i);
        zzz = prova1*prova2;
        P2_x (j,i) = zzz;
     end
end
%%

r_vec_3sh   = repmat(r_vec_2sh,[N_h*N_y,1]);
h_vec_2sh   = repmat(h_vec,[N_y,1]);
y_vec_2sh   = kron(y_vec,ones(N_h,1));

[h_grid,  y_grid] = meshgrid(h_vec,  y_vec);

qrf_vec = (1 + r_vec_3sh).^-(1); % Make yearly interest rates into quarterly debt prices
qrf_lt = qrf_vec(1)/(1-(1-delta)*qrf_vec(1));


%% Define utility under autarky

if def_cost_asymm==1
c_aut =  h_vec_2sh.*y_vec_2sh;    
c_aut(c_aut>wc_par_asymm*gdp_mean) = wc_par_asymm*gdp_mean;
elseif def_cost_asymm==0
c_aut = wc_par_symm*h_vec_2sh.*y_vec_2sh;
elseif def_cost_asymm==2
c_aut = y_vec_2sh - max(0,cost1f.*y_vec_2sh+cost2f.*y_vec_2sh.^2);
c_aut = h_vec_2sh.*c_aut;
end

util_aut = 1/(1-gamma_c)*c_aut.^(1-gamma_c);

%% Here begins dynamic sovereign default problem

% Parameters for iteration
damp_v        = .8;          % dampening in vfi
damp_q        = .8;          % dampening in q-update
maxiter_v   = 300;
maxiter_q   = 300;
tol_v       = 1e-4;
tol_q       = 1e-6;
log_diff_q      = [];

iter_v  = 1;
iter_q  = 1;
diff_v  = 7;
diff_q  = 7;
sum_v   = 7;

loadguesses     = 0;    % 1 if loading guesses from external file

%Value function shocks
ev_rho = 1e-2;
ev_rho_def = 1/ev_rho;
eulgam = 0.5772;%double(eulergamma);


% Define grid for government debt ------

single_space    = 0;    % 1 if grid is evenly spaced, 0 if 2-steps grid

b_g_min   = -0.05;
b_g_max   = 1.18;%.2335;%4;

if single_space
    
    b_g_vec = linspace(b_g_min,b_g_max,N_b_g);
    
else
    
     b_g_mid = .3;
    N_b_g_mid = floor(.85*N_b_g);
    
    
low_bound =b_g_min;
mid_point =b_g_mid;
upp_bound =b_g_max;
N_1 =N_b_g_mid;
N_tot =N_b_g;

if N_1 > 0 && N_1 < N_tot && ( (low_bound < mid_point && mid_point < upp_bound) || (low_bound > mid_point && mid_point > upp_bound) )

y_1 = linspace(low_bound,mid_point,N_1);

y_2 = linspace(mid_point+(upp_bound-mid_point)/(N_tot-N_1),upp_bound,N_tot-N_1);

b_g_vec = [y_1 y_2];

else
    
b_g_vec = linspace(low_bound,upp_bound,N_tot);

end
    
end

% Ensure presence of 0 on b-vector
[~,i_b_g_zero] = min(abs(b_g_vec));
b_g_vec(i_b_g_zero) = 0;

% 3-dimensional grid for state-debt. Dim: x,b,b'
b_state_grid = repmat(b_g_vec,[N_x,1,N_b_g]);

% 2-dimensional grid for choice-debt. Dim: x,b'
b_choice_2grid = repmat(b_g_vec,[N_x,1]);

% 3-dimensional grid for y-state. Dim: x,b,b'
y_state_grid = repmat(y_vec_2sh,[1,N_b_g,N_b_g]);

% 3-dimensional grid for h-state. Dim: x,b,b'
h_state_grid = repmat(h_vec_2sh,[1,N_b_g,N_b_g]);

% -------------------------------------------------

%% DO NOT RUN IF ADJUSTING GRIDS

% Pre-allocate grids
% tau_choice      = NaN(N_x,N_b_g,N_b_g);
% util_choice     = NaN(N_x,N_b_g,N_b_g);

% Temporary policy functions for tau and price index
% tau_pf_temp = NaN(N_x,N_b_g);
% p_pf_temp   = NaN(N_x,N_b_g);

if loadguesses
    
    load('new_guesses')
    
else
    
    % Form initial guesses
    q_g = qrf_lt*ones(N_x,N_b_g);
    q_g_rel = qrf_lt*ones(N_x,N_b_g);
    q_g2 = qrf_lt*ones(N_x,N_b_g);
    v_guess = zeros(N_x,N_b_g);
%     p_g_choice_guess = p_bar * ones(N_x,N_b_g,N_b_g);
    v_bad_guess = zeros(N_x,1);
    v_rel_guess = zeros(N_x,N_b_g);
    i_b_max_new = NaN(N_x,N_b_g);
    def_new= NaN(N_x,N_b_g);
    rel_new= zeros(N_x,N_b_g);
    
end

q_g_pf = zeros(N_x,N_b_g);
q_g_rel_pf = zeros(N_x,N_b_g);
q_g_pf2 = zeros(N_x,N_b_g);

dummy_rel = ones(N_x,N_b_g);
dummy_rel = reshape(dummy_rel,N_h,N_y,N_b_g);
dummy_rel(1,:,:) = zeros;
dummy_rel = reshape(dummy_rel,N_x,N_b_g);

%%



while diff_q > tol_q && iter_q < maxiter_q


while diff_v > tol_v && iter_v<maxiter_v && sum_v>1
    
    % Expected continuation value
    e_v_guess = P_x*v_guess;
    e_v_guess_3grid = permute(repmat(e_v_guess,[1 1 N_b_g]),[1 3 2]);
    
    
    % value if re-entering contract with no debt
    v_badgood_guess = v_guess(:,i_b_g_zero);
    e_v_badgood_guess = P_x*v_badgood_guess;
    
    % Expected value of remaining in exclusion state
    e_v_bad_guess = P_x*v_bad_guess;
    
    e_v_rel_guess = P_x*v_rel_guess;
    e_v_rel_guess_3grid = permute(repmat(e_v_rel_guess,[1 1 N_b_g]),[1 3 2]);   
 
    
    % Resources from borrowing
    borr_rev_choice_3grid = permute(repmat(q_g,[1,1,N_b_g]),[1 3 2]).*...
        (permute(repmat(b_choice_2grid,[1,1,N_b_g]),[1 3 2])-(1-delta).*b_state_grid);
    
    borr_rev_choice_3grid_rel = permute(repmat(q_g,[1,1,N_b_g]),[1 3 2]).*...
        (permute(repmat(b_choice_2grid,[1,1,N_b_g]),[1 3 2])-share.*(1-delta).*b_state_grid-(1-share).*(1+mu_r).*b_state_grid);

    
    % Consumption implied by state and choice for b'. Une a guess for price index. Dim: z,b,b'
    cons_choice = h_state_grid.*y_state_grid - b_state_grid + borr_rev_choice_3grid;
    cons_choice(cons_choice<eps) = eps;

    
   % Consumption under hurricane relief
    cons_rel_choice = h_state_grid.*y_state_grid- share.*b_state_grid+borr_rev_choice_3grid_rel;
    cons_rel_choice(cons_rel_choice<eps) = eps;

    
    % Period-utility implied by state and choice for b'. Dim: z,b,b'
    util_choice = 1/(1-gamma_c)*cons_choice.^(1-gamma_c);
    util_rel_choice = 1/(1-gamma_c)*cons_rel_choice.^(1-gamma_c);
        
    % Form maximand in borrowing choice
    borrower_maximand = util_choice + beta*e_v_guess_3grid;
    borrower_maximand_rel = util_rel_choice + beta*e_v_guess_3grid;
     % Choice for borrowing and update value function

     [v_good_guess_noev, i_b_max_new_noev] = max(borrower_maximand,[],3);
     [v_good_guess_noev_rel, i_b_max_new_noev_rel] = max(borrower_maximand_rel,[],3);
% v_good_guess_noev_rel=zeros(size(v_good_guess_noev,1),size(v_good_guess_noev,2));
%     for cicci=1:N_x
%         for cicci1 = 1:N_b_g
%     v_good_guess_noev_rel(cicci,cicci1) = borrower_maximand_rel(cicci,cicci1,i_b_max_new_noev(cicci,cicci1));
%         end
%     end
    % Compute choice probabilities with EV shocks
    prob_choice = exp((borrower_maximand-repmat(v_good_guess_noev,[1,1,N_b_g]))/ev_rho)...
        ./sum(exp((borrower_maximand-repmat(v_good_guess_noev,[1,1,N_b_g]))/ev_rho),3);
    
    prob_choice_rel = exp((borrower_maximand_rel-repmat(v_good_guess_noev_rel,[1,1,N_b_g]))/ev_rho)...
        ./sum(exp((borrower_maximand_rel-repmat(v_good_guess_noev_rel,[1,1,N_b_g]))/ev_rho),3);
    
    norma_explog = repmat(v_good_guess_noev,[1,1,N_b_g]);
    norma_explog_rel = repmat(v_good_guess_noev_rel,[1,1,N_b_g]);
    
    v_good_guess_new = eulgam*ev_rho + ...
        v_good_guess_noev + ...
        ev_rho*log(sum(exp(1/ev_rho*(borrower_maximand-norma_explog)),3));
  
    v_good_guess_new_rel = eulgam*ev_rho + ...
        v_good_guess_noev_rel + ...
        ev_rho*log(sum(exp(1/ev_rho*(borrower_maximand_rel-norma_explog_rel)),3));
    
    % Evaluate value function in default state
    v_bad_guess_new = util_aut + beta*(lambda*e_v_badgood_guess + (1-lambda)*e_v_bad_guess);
    
    %Update policy function
    v_guess_new = eulgam*ev_rho + v_good_guess_new + ...
        ev_rho*log(1+exp(1/ev_rho*(-v_good_guess_new+repmat(v_bad_guess_new,[1,N_b_g]))));

    v_guess_new_rel = eulgam*ev_rho + v_good_guess_new_rel + ...
        ev_rho*log(1+exp(1/ev_rho*(-v_good_guess_new_rel+repmat(v_bad_guess_new,[1,N_b_g]))));   
    
    %Value function in default
    v_guess_new_flip = eulgam*ev_rho + repmat(v_bad_guess_new,[1,N_b_g]) + ...
        ev_rho*log(1+exp(1/ev_rho*(+v_good_guess_new-repmat(v_bad_guess_new,[1,N_b_g]))));
    
    v_guess_new_flip_rel = eulgam*ev_rho + repmat(v_bad_guess_new,[1,N_b_g]) + ...
        ev_rho*log(1+exp(1/ev_rho*(+v_good_guess_new_rel-repmat(v_bad_guess_new,[1,N_b_g]))));   
    



    %Store old default policy function
    def_old = def_new;
    rel_old = rel_new;
    
    %Ask for relief
%     rel_new = (1-(exp(ev_rho_def*(v_good_guess_new_rel-v_good_guess_new))+1).^-1);
%     rel_new((1-(exp(ev_rho_def*(v_bad_guess_new -v_good_guess_new_rel))+1).^-1)>0.999)=0;
% %     rel_new(v_rel_good_guess_new<repmat(v_bad_guess_new,[1,N_b_g])) = 0;
%     %Only provide relief where you would default
% %     rel_new( (1-(exp(ev_rho_def*(repmat(v_bad_guess_new,[1,N_b_g])-v_good_guess_new))+1).^-1)<0.999) = 0; 
%     rel_new(dummy_rel==0) = 0;
    rel_new = zeros(N_x,N_b_g);
    rel_new(dummy_rel==1) = 1;


 


    % Evaluate policy function for default
    def_new = 1-(exp(ev_rho_def*(repmat(v_bad_guess_new,[1,N_b_g])-v_good_guess_new))+1).^-1;
    def_new(dummy_rel==1)=0;
    
    def_new_rel = 1-(exp(ev_rho_def*(v_bad_guess_new-v_good_guess_new_rel))+1).^-1;
    def_new_rel(dummy_rel==0)=0;
    
    
    %Adjust also the rel value function
  
    v_guess_new(def_new>.999)=v_guess_new_flip(def_new>.999);    
    v_guess_new_rel(def_new_rel>.999)=v_guess_new_flip_rel(def_new_rel>.999);   
    
    v_guess_new(dummy_rel==1) = v_guess_new_rel(dummy_rel==1);
    v_guess_new_rel(dummy_rel==0) = v_guess_new(dummy_rel==0);
    

    def_new = def_new+def_new_rel;
    
%     v_guess_new_rel(rel_new<=.999  & def_new_rel<=.999)=v_guess_new(rel_new<=.999  & def_new_rel<=.999);
%     v_guess_new_rel(rel_new>.999 & def_new_rel>.999)= v_guess_new_flip_rel(rel_new>.999 & def_new_rel>.999);
%     
%     %Replace the value function for default when government is in default
%     v_guess_new(rel_new>.999)=v_guess_new_rel(rel_new>.999);
%     v_guess_new_rel(dummy_rel==1) = v_guess_new(dummy_rel==1);

    
    
    % Store old value-function guesses
    v_old = v_guess;
    v_bad_old = v_bad_guess;
    v_rel_old = v_rel_guess;
    
    % Update value-function guesses
    v_guess = damp_v*v_guess_new + (1-damp_v)*v_old;
    v_bad_guess = damp_v*v_bad_guess_new + (1-damp_v)*v_bad_old;
    v_rel_guess = damp_v*v_guess_new_rel + (1-damp_v)*v_rel_old;
    
    % Evaluate change in v
    diff_v = max(abs(v_guess_new(:)-v_old(:)));
    sum_v = sum((abs(v_guess_new(:)-v_old(:)))>1e-4);

    iter_v = iter_v+1;
    
end

% [~,i_b_max_prob_choice]  = max(prob_choice,[],3);
% prob_choice_rel = zeros(N_x, N_b_g,N_b_g);
% for i=1:N_x
%     for j = 1:N_b_g
%         prob_choice_rel(i,j,i_b_max_prob_choice(i,j))=1;
%     end
% end
%Default
rel_only_pf = rel_new;
def_only_pf = def_new;

% Policy function for q_g
q_g_pf_old = q_g_pf;
q_g_rel_pf_old = q_g_rel_pf;
q_g_pf_old2 = q_g_pf2;

q_g_pf = NaN(N_x,N_b_g);
q_g_rel_pf = NaN(N_x,N_b_g);
q_g_rel_rel_pf = NaN(N_x,N_b_g);
q_g_pf2 = NaN(N_x,N_b_g);
q_g_rel_pf2 = NaN(N_x,N_b_g);
for i_x = 1:N_x
for i_b = 1:N_b_g
    q_g_pf(i_x,i_b) = sum(q_g(i_x,:)'.*squeeze(prob_choice(i_x,i_b,:)));
    q_g_rel_pf(i_x,i_b) = sum(q_g(i_x,:)'.*squeeze(prob_choice_rel(i_x,i_b,:)));
    q_g_rel_rel_pf(i_x,i_b) = sum(q_g_rel(i_x,:)'.*squeeze(prob_choice_rel(i_x,i_b,:)));
    q_g_pf2(i_x,i_b) = sum(q_g2(i_x,:)'.*squeeze(prob_choice(i_x,i_b,:)));
    q_g_rel_pf2(i_x,i_b) = sum(q_g2(i_x,:)'.*squeeze(prob_choice_rel(i_x,i_b,:)));
end
end


% PF for q_g, with zeros where there are NaN's - this could be killed
q_g_pf_zeros = q_g_pf;
q_g_pf_zeros(isnan(q_g_pf)) = 0;

% q_g_rel_pf =  (1-def_only_pf-rel_only_pf).*q_g_pf;
% Default probability conditional on debt choice
e_defrel = P_x*((1-def_only_pf).*(1-rel_only_pf).*(1+(1-delta).*q_g_pf_zeros)...
   +(1-def_only_pf).*rel_only_pf.*(share.*(1+(1-delta).*q_g_pf_zeros) +(1-share).*(1+mu_r).*q_g_rel_pf));

e_defrel_re = P_x*((1-def_only_pf).*(1-rel_only_pf).*(1+(1-delta).*q_g_rel_rel_pf)...
   +(1-def_new_rel).*rel_only_pf.*(share.*(1+(1-delta).*q_g_rel_rel_pf)+(1-share).*(1-0.*delta).*q_g_rel_rel_pf));


e_defrel2 = P_x*((1-def_only_pf).*(1-rel_only_pf).*(1+(1-delta).*q_g_pf_zeros)...
   +(1-def_only_pf).*rel_only_pf.*(share.*(1+(1-delta).*q_g_pf_zeros)+(1-share).*(1+(1-delta).*qrf_lt)));





% Compute new sovereign debt price
q_g_new = repmat(qrf_vec,[1,N_b_g]).*(e_defrel);
q_g_new = max(0,q_g_new);
% Impose RF debt price if buying assets
q_g_new(:,b_g_vec<=0) = qrf_lt;


q_g_rel_new = repmat(qrf_vec,[1,N_b_g]).*(e_defrel_re);
q_g_rel_new = max(0,q_g_rel_new);
% Impose RF debt price if buying assets
q_g_rel_new(:,b_g_vec<=0) = qrf_lt;


q_g_new2 = repmat(qrf_vec,[1,N_b_g]).*(e_defrel2);
q_g_new2 = max(0,q_g_new2);
% Impose RF debt price if buying assets
q_g_new2(:,b_g_vec<=0) = qrf_lt;

% Store old sovereign debt price
q_g_old = q_g;
q_g_old2 = q_g2;
q_g_rel_old = q_g_rel;

% Evaluate change in q_g
diff_q = max(abs(q_g_new(:)-q_g_old(:)))

% Update sovereign debt price
q_g = damp_q*q_g_new + (1-damp_q)*q_g_old;
q_g_rel = damp_q*q_g_rel_new + (1-damp_q)*q_g_rel_old;
% Update sovereign debt price
q_g2 = damp_q*q_g_new2 + (1-damp_q)*q_g_old2;




iter_q

iter_q = iter_q + 1;

iter_v

% Reset counter and diff for inner-v loop
diff_v = 7;
sum_v = 7;
iter_v = 1;


end


%% Simulate


size_grid = [N_h N_y]; 

% Number of simulated periods
T_sim = 10000;
counter=1;

filename_guess = 'climate_persistent_wf';
lg = load(filename_guess);

redem_sim     = lg.redem_sim_counter(:,counter);
i_x_sim = lg.i_x_sim_counter(:,counter);  
V_g_mean_baseline  = lg.V_g_mean_counter(:,counter);
%%


% Pre-allocate for speed
T_sim1 = T_sim-1;
dist_sim = zeros(N_x,N_b_g,T_sim+1);
mass_acc = zeros(T_sim,1);
prova= NaN(T_sim1,1); 
r_g_mean = zeros(T_sim,1);
r_g_mean2 = zeros(T_sim,1);
q_g_mean = zeros(T_sim,1);
q_g_mean2 = zeros(T_sim,1);
b_g_mean = zeros(T_sim,1);    
y_sim = y_vec_2sh(i_x_sim(1:T_sim,1));
h_sim = h_vec_2sh(i_x_sim(1:T_sim,1));
V_g_mean = zeros(T_sim,1);

dist_sim(i_x_sim(1,1),i_b_g_zero,1) = 1;
mass_acc(1,1)=1;
mass_only_rel(1,1)=1;
mass_only_def(1,1)=1;
rel_only_pf(def_only_pf>0.999)=0;    
for t_sim = 1:T_sim1
      %Neither default nor debt relief
     if  mass_only_def(t_sim,1)>0.99 && floor((i_x_sim(t_sim,1)-1)./N_h)==(i_x_sim(t_sim,1)-1)./N_h
         prova(t_sim,1)=1;
    mass_only_def(t_sim+1,1) = sum(sum(dist_sim(:,:,t_sim).*(1-def_only_pf).*(1-rel_only_pf))); %def_pf already includes reliefs
       
    % Evolution of distribution of countries, given probabilistic decision
    % rule and exogenous income shocks
    dist_sim(i_x_sim(t_sim+1,1),:,t_sim+1) = sum(sum(repmat(dist_sim(:,:,t_sim).*...
        (1-def_only_pf).*(1-rel_only_pf),[1,1,N_b_g]).*prob_choice,1) ,2);
       
    r_g_mean(t_sim) = sum(sum(((1+1./q_g_pf-delta).^1-1).*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
%     r_g_mean2(t_sim) = sum(sum(((1+1./q_g_pf2-delta).^1-1).*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
    q_g_mean(t_sim) = sum(sum(q_g_pf.*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
%     q_g_mean2(t_sim) = sum(sum(q_g_pf2.*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
    b_g_mean(t_sim) = sum(sum(repmat(b_g_vec,[N_x,1]).*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
%     V_g_mean(t_sim) = sum(sum(v_guess.*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));

     elseif  mass_only_def(t_sim,1)>0.99 && floor((i_x_sim(t_sim,1)-1)./N_h)~=(i_x_sim(t_sim,1)-1)./N_h
         prova(t_sim,1)=2;
    mass_only_def(t_sim+1,1) = sum(sum(dist_sim(:,:,t_sim).*(1-def_only_pf).*rel_only_pf)); %def_pf already includes reliefs
       
    % Evolution of distribution of countries, given probabilistic decision
    % rule and exogenous income shocks
    dist_sim(i_x_sim(t_sim+1,1),:,t_sim+1) = sum(sum(repmat(dist_sim(:,:,t_sim).*...
        (1-def_only_pf).*rel_only_pf,[1,1,N_b_g]).*prob_choice,1)  ,2);
       
    r_g_mean(t_sim) = sum(sum(((1+1./q_g_pf-delta).^1-1).*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
%     r_g_mean2(t_sim) = sum(sum(((1+1./q_g_pf2-delta).^1-1).*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
    q_g_mean(t_sim) = sum(sum(q_g_pf.*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
%     q_g_mean2(t_sim) = sum(sum(q_g_pf2.*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
    b_g_mean(t_sim) = sum(sum(repmat(b_g_vec,[N_x,1]).*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
%     V_g_mean(t_sim) = sum(sum(v_guess_new_rel.*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));

    
    %Default
    elseif mass_only_def(t_sim,1)<=0.99 
         prova(t_sim,1)=3;
    mass_only_def(t_sim+1,1) = redem_sim(t_sim+1,1); %def_pf already includes reliefs

    dist_sim(i_x_sim(t_sim+1,1),i_b_g_zero,t_sim+1) = 1;
    r_g_mean(t_sim)=NaN;
    r_g_mean2(t_sim)=NaN;
    q_g_mean(t_sim)=NaN;
%     q_g_mean2(t_sim)=NaN;
    b_g_mean(t_sim)=NaN;
%     V_g_mean(t_sim) = v_bad_guess(i_x_sim(t_sim,1),1);
    end
end

b_g_mean_counter(:,counter,share_counter) = b_g_mean; %Save the path of debt
B_g_sim = (1./(y_sim.*h_sim)).*(b_g_mean(:)./(delta+mu_r));
B_g_sim_market = (1./(y_sim.*h_sim)).*(b_g_mean(:)./(delta+r_g_mean));

spread_sim = 10000*((1+r_g_mean)./(1+r_vec)-1);
spread_sim2 = 10000*((1+r_g_mean)./(1+r_g_mean2)-1);
spread_sim_counter(:,counter,share_counter)=spread_sim;
spread_sim_counter2(:,counter,share_counter)=spread_sim2;

b_g_sim1 = b_g_mean(1:end-1,:);
b_g_sim1 = [b_g_sim1;NaN];
b_g_sim_curr = b_g_mean(2:end,:);
b_g_sim_curr = [NaN; b_g_sim_curr];

nx_sim  = -q_g_mean.*(b_g_sim_curr-(1-delta).*b_g_sim1)+b_g_sim1;
nx_sim(isnan(nx_sim)==1)=0; %Excluded from the market
c_sim1 = y_sim.*h_sim-nx_sim;
c_sim = c_sim1;
c_sim(mass_only_def<=0.99 )=wc_par_asymm*gdp_mean;
cons_sim(:,counter,share_counter)=c_sim;

%Statistics
meanBY_sim(counter,share_counter)= nanmean(B_g_sim(spread_sim<1e+4));
meanBY_sim_market(counter,share_counter)= nanmean(q_g_mean(spread_sim<1e+4).*b_g_mean(spread_sim<1e+4));
meanspread_sim(counter,share_counter)= nanmean(spread_sim(spread_sim<1e+4));
meanspread_sim2(counter,share_counter)= nanmean(spread_sim2(spread_sim2<1e+4));
stdspread_sim(counter,share_counter) = std(spread_sim(spread_sim<1e+4),0,1,'omitnan');
stdspread_sim2(counter,share_counter) = std(spread_sim2(spread_sim2<1e+4),0,1,'omitnan');
hur_freq_sim(counter,share_counter)  = size(h_sim(h_sim<1),1)./size(h_sim,1);

%Default Incidence
B_g_sim2 = B_g_sim(1:end-1);
B_g_sim2 = [110;B_g_sim2];
def_sim = zeros(T_sim,1);
def_sim(isnan(B_g_sim)==1 &  isnan(B_g_sim2)==0)=1;
def_freq_sim(counter,share_counter)  = mean(def_sim);
def_hur_freq_sim(counter,share_counter)  = nanmean(def_sim(h_sim<1));

%GDP Loss|Hurricane
gdp_sim =y_sim.*h_sim;
gdp_sim(isnan(c_sim1)==1)=gdp_mean;
gdp_g = (gdp_sim(2:end,1)-gdp_sim(1:end-1))./gdp_sim(1:end-1);
gdp_g_h_sim(counter,share_counter) = mean(gdp_g(h_sim(2:end,1)<1));


%Spread Increase|Hurricane
spread_g = (spread_sim(2:end,1)-spread_sim(1:end-1))./spread_sim(1:end-1);
spread_g_h_sim(counter,share_counter) = nanmedian(spread_g(h_sim(2:end,1)<1));


%Consumption equivalent welfare change according to value function
V_g_mean_baseline(V_g_mean_baseline==0)  = NaN;
V_g_mean(V_g_mean==0)  = NaN;

prova =nanmean(V_g_mean_baseline);
prova1 =nanmean(V_g_mean);

prova2 = ((prova1./prova).^(1./(1-2)))-1;
conequivwc_V_counter(counter,share_counter)  = nanmean(nanmean(prova2));
%%
  
clearvars -except zz jj string_num meanBY_sim  meanBY_sim_market meanspread_sim y_vec_2sh...
    h_vec_2sh P_x q_g q_g_pf  q_g_pf2 def_only_pf rel_only_pf prob_choice prob_choice_rel...
    N_x N_h N_y N_b_g b_g_vec...
    delta mu_r b_g_vec i_b_g_zero v_bad_guess v_guess v_guess_new_rel prob_choice_rel
 

save('climate_w_clause_persistent_antiguafull.mat')

    end
    share_counter=share_counter+1;
end

