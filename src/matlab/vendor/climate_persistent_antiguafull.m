% clear all

cc_freq =1;
cc_int = 1;
        
% if counter==1 %Antigua
% y-process parameters
sigma_ey = .046;%.006;         % Standard deviation of innovation of y. Arellano = 0.025
rho_y    = .92;%.98;          % AR coefficient for y. Arellano = 0.945
beta     =  .915;% .9;          % Subjective discount factor (Cuadra, Sanchez, Sapriza = .97) Arellano: .953
wc_par_asymm   = .75;%.8;
delta = 0.0824;% (8.2 years maturity)
sigma_eh = .029;%.006;         % Standard deviation of hurricane
mean_h    = 1-cc_int.*0.049;%.98;          % Average GDP loss with hurricane hit
p_hu = cc_freq.*0.103; %You are hit by a hurricane once every 14.8 years

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

gdp_mean = (P_x^100000*(kron(y_vec,ones(N_h,1)).*(kron(ones(N_y,1),h_vec))));
gdp_mean = gdp_mean(floor(N_y*N_h/2)+1);


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
maxiter_q   = 600;
tol_v       = 1e-3;
tol_q       = 1e-6;
log_diff_q      = [];

iter_v  = 1;
iter_q  = 1;
diff_v  = 7;
diff_q  = 7;

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
    v_guess = zeros(N_x,N_b_g);
%     p_g_choice_guess = p_bar * ones(N_x,N_b_g,N_b_g);
    v_bad_guess = zeros(N_x,1);
    i_b_max_new = NaN(N_x,N_b_g);
    def_new= NaN(N_x,N_b_g);
    
end

q_g_pf = zeros(N_x,N_b_g);


%% Sovereign Default Iteration
iter_q=1;

while diff_q > tol_q && iter_q < maxiter_q

    %Store old default policy function
def_old = def_new;

while diff_v > tol_v && iter_v<maxiter_v
    
    % Expected continuation value
    e_v_guess = P_x*v_guess;
    e_v_guess_3grid = permute(repmat(e_v_guess,[1 1 N_b_g]),[1 3 2]);
    
    % value if re-entering contract with no debt
    v_badgood_guess = v_guess(:,i_b_g_zero);
    e_v_badgood_guess = P_x*v_badgood_guess;
    
    % Expected value of remaining in exclusion state
    e_v_bad_guess = P_x*v_bad_guess;
    
    % Resources from borrowing
    borr_rev_choice_3grid = permute(repmat(q_g,[1,1,N_b_g]),[1 3 2]).*...
        (permute(repmat(b_choice_2grid,[1,1,N_b_g]),[1 3 2])-(1-delta).*b_state_grid);
    
    % Consumption implied by state and choice for b'. Dim: z,b,b'
    cons_choice = h_state_grid.*y_state_grid - b_state_grid + borr_rev_choice_3grid;
    cons_choice(cons_choice<eps) = eps;
    
    util_choice = 1/(1-gamma_c)*cons_choice.^(1-gamma_c);
        
    % Form maximand in borrowing choice
    borrower_maximand = util_choice + beta*e_v_guess_3grid;   
    
    % Choice for borrowing and update value function
    [v_good_guess_noev, i_b_max_new_noev] = max(borrower_maximand,[],3);
    
    % Compute choice probabilities with EV shocks
    prob_choice = exp((borrower_maximand-repmat(v_good_guess_noev,[1,1,N_b_g]))/ev_rho)...
        ./sum(exp((borrower_maximand-repmat(v_good_guess_noev,[1,1,N_b_g]))/ev_rho),3);
    
    norma_explog = repmat(v_good_guess_noev,[1,1,N_b_g]);
    
    v_good_guess_new = eulgam*ev_rho + ...
        v_good_guess_noev + ...
        ev_rho*log(sum(exp(1/ev_rho*(borrower_maximand-norma_explog)),3));
  
    
    % Evaluate value function in default state
    v_bad_guess_new = util_aut + beta*(lambda*e_v_badgood_guess + (1-lambda)*e_v_bad_guess);
    
    
    % Evaluate policy function for default
    def_new = 1-(exp(ev_rho_def*(repmat(v_bad_guess_new,[1,N_b_g])-v_good_guess_new))+1).^-1;
    
    % Evaluate value function including discrete choice for default
    v_guess_new = eulgam*ev_rho + v_good_guess_new + ...
        ev_rho*log(1+exp(1/ev_rho*(-v_good_guess_new+repmat(v_bad_guess_new,[1,N_b_g]))));
    
    v_guess_new_flip = eulgam*ev_rho + repmat(v_bad_guess_new,[1,N_b_g]) + ...
        ev_rho*log(1+exp(1/ev_rho*(+v_good_guess_new-repmat(v_bad_guess_new,[1,N_b_g]))));
    
    v_guess_new(def_new>.999)=v_guess_new_flip(def_new>.999);

    % Store old value-function guesses
    v_old = v_guess;
    v_bad_old = v_bad_guess;
    
    % Update value-function guesses
    v_guess = damp_v*v_guess_new + (1-damp_v)*v_old;
    v_bad_guess = damp_v*v_bad_guess_new + (1-damp_v)*v_bad_old;
    
    % Evaluate change in v
    diff_v = max(abs(v_guess_new(:)-v_old(:)))
    
    iter_v = iter_v+1;
    
end

diff_v
iter_v

% ---- Compute some policy functions

%Default
def_pf = def_new;

% Debt - index
% i_b_g_pf = i_b_max_new;
% i_b_g_pf(def_pf>.9) = i_b_g_zero;

% Policy function for q_g
q_g_pf_old = q_g_pf;
q_g_pf = NaN(N_x,N_b_g);
for i_x = 1:N_x
for i_b = 1:N_b_g
q_g_pf(i_x,i_b) = sum(q_g(i_x,:)'.*squeeze(prob_choice(i_x,i_b,:)));
end
end

% PF for q_g, with zeros where there are NaN's - this could be killed
q_g_pf_zeros = q_g_pf;
q_g_pf_zeros(isnan(q_g_pf)) = 0;


% Default probability conditional on debt choice
e_def = P_x*def_new;
e_deflong = P_x*((1-def_new).*q_g_pf_zeros); %P_x*((1-def_new).*q_g);

% Compute new sovereign debt price
q_g_new = repmat(qrf_vec,[1,N_b_g]).*(1-e_def)+(1-delta).*repmat(qrf_vec,[1,N_b_g]).*(e_deflong);
q_g_new = max(0,q_g_new);
% Impose RF debt price if buying assets
q_g_new(:,b_g_vec<=0) = qrf_lt;
% Store old sovereign debt price
q_g_old = q_g;


% Evaluate change in q_g
diff_q = max(abs(q_g_new(:)-q_g_old(:)))

% Update sovereign debt price
q_g = damp_q*q_g_new + (1-damp_q)*q_g_old;


log_diff_q = [log_diff_q diff_q]; 
iter_q
iter_q = iter_q + 1;

% Reset counter and diff for inner-v loop
diff_v = 7;
iter_v = 1;
end


%% Simulate

size_grid = [N_h N_y]; 

% Number of simulated periods
T_sim = 10000;
init_x_sim = sub2ind(size_grid,floor(N_h/2)+1,floor(N_y/2)+1);



    
 % Simulated shock process
    %%
T=P_x;
n=T_sim;
s0=init_x_sim;
V=1:N_x;

%
[r c]=size(T);

%
if r ~= c;
  disp('error using markov function');
  disp('transition matrix must be square');
  return;
end;
%
for k=1:r;
  if sum(T(k,:)) ~= 1;
    disp('error using markov function')
    disp(['row ',num2str(k),' does not sum to one']);
    disp(['normalizing row ',num2str(k),'']);
    T(k,:)=T(k,:)/sum(T(k,:));
  end;
end;
[v1 v2]=size(V);
if v1 ~= 1 |v2 ~=r
  disp('error using markov function');
  disp(['state value vector V must be 1 x ',num2str(r),''])
  if v2 == 1 &v2 == r;
    disp('transposing state valuation vector');
    V=V';
  else;
    return;
  end;  
end
if s0 < 1 |s0 > r;
  disp(['initial state ',num2str(s0),' is out of range']);
  disp(['initial state defaulting to 1']);
  s0=1;
end;
%
%T
%rand('uniform');
X=rand(n-1,1);
s=zeros(r,1);
s(s0)=1;
cum=T*triu(ones(size(T)));
%
for k=1:length(X);
  state(:,k)=s;
  ppi=[0 s'*cum];
  s=((X(k)<=ppi(2:r+1)).*(X(k)>ppi(1:r)))';
end;
i_x_sim=V*state;
    
i_x_sim = [init_x_sim i_x_sim]';

% Simulated redemption process
redem_sim = (rand(T_sim+1,1)<lambda);
    


% load shocks_climate_wf;
% load bpath_def_hur_climate_wf;
% redem_sim = redem_sim_counter(1:T_sim,counter);
% i_x_sim = i_x_sim_counter(:,counter);   


%%

% Pre-allocate for speed
T_sim1 = T_sim-1;
dist_sim = zeros(N_x,N_b_g,T_sim+1);

% dist_sim_curr = zeros(N_x,N_b_g);
% dist_sim_next = zeros(N_x,N_b_g);
mass_acc = zeros(T_sim,1);
access_sim      = NaN(T_sim1,1); % Access to int'l financial markets
r_g_mean = zeros(T_sim,1);
q_g_mean = zeros(T_sim,1);
b_g_mean = zeros(T_sim,1);    
y_sim = y_vec_2sh(i_x_sim(1:T_sim,1));
h_sim = h_vec_2sh(i_x_sim(1:T_sim,1));

access_sim(1,1)   = 1;
dist_sim(i_x_sim(1,1),i_b_g_zero,1) = 1;
mass_acc(1,1)=1;
    
for t_sim = 1:T_sim1
    
    if mass_acc(t_sim,1)>0.99 % Access to international financial markets
        
    mass_acc(t_sim+1,1) = sum(sum(dist_sim(:,:,t_sim).*(1-def_pf)));
       
    % Evolution of distribution of countries, given probabilistic decision
    % rule and exogenous income shocks
    dist_sim(i_x_sim(t_sim+1,1),:,t_sim+1) = sum(sum(repmat(dist_sim(:,:,t_sim).*...
        (1-def_pf),[1,1,N_b_g]).*prob_choice,1),2);
    
    
    r_g_mean(t_sim) = sum(sum(((1+1./q_g_pf-delta).^1-1).*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
    q_g_mean(t_sim) = sum(sum(q_g_pf.*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));
    b_g_mean(t_sim) = sum(sum(repmat(b_g_vec,[N_x,1]).*dist_sim(:,:,t_sim)))./sum(sum(dist_sim(:,:,t_sim)));


        
    else    % Financial autarky
        
    mass_acc(t_sim+1,1) = redem_sim(t_sim+1,1);
    dist_sim(i_x_sim(t_sim+1,1),i_b_g_zero,t_sim+1) = 1;
    r_g_mean(t_sim)=NaN;
    q_g_mean(t_sim)=NaN;
    b_g_mean(t_sim)=NaN;
    end
end
B_g_sim = (1./(y_sim.*h_sim)).*(b_g_mean(:)./(delta+mu_r));
spread_sim = 10000*((1+r_g_mean)./(1+r_vec)-1);

b_g_sim1 = b_g_mean(1:end-1,:);
b_g_sim1 = [b_g_sim1;NaN];
b_g_sim_curr = b_g_mean(2:end,:);
b_g_sim_curr = [NaN; b_g_sim_curr];

nx_sim  = -q_g_mean.*(b_g_sim_curr-(1-delta).*b_g_sim1)+b_g_sim1;
nx_sim(isnan(nx_sim)==1)=0; %Excluded from the market
c_sim = y_sim.*h_sim-nx_sim;
c_sim(isnan(c_sim)==1)=gdp_mean;
% cons_sim(:,counter)=c_sim;

%Statistics
meanBY_sim= nanmean(B_g_sim(spread_sim<1e+4));
meanBY_sim_market= nanmean(q_g_mean(spread_sim<1e+4).*b_g_mean(spread_sim<1e+4));
meanspread_sim= nanmean(spread_sim(spread_sim<1e+4));
h_freq_sim= size(h_sim(h_sim<1),1)./size(h_sim,1);


%Default Incidence
B_g_sim2 = B_g_sim(1:end-1);
B_g_sim2 = [110;B_g_sim2];
def_sim = zeros(T_sim,1);
def_sim(isnan(B_g_sim)==1 &  isnan(B_g_sim2)==0)=1;
def_freq_sim = mean(def_sim);

%GDP Loss|Hurricane
gdp_sim =y_sim.*h_sim;
gdp_sim(isnan(c_sim)==1)=gdp_mean;
gdp_g = (gdp_sim(2:end,1)-gdp_sim(1:end-1))./gdp_sim(1:end-1);
gdp_g_h_sim = mean(gdp_g(h_sim(2:end,1)<1));

%Spread Increase|Hurricane
spread_g = (spread_sim(2:end,1)-spread_sim(1:end-1))./spread_sim(1:end-1);
spread_g_h_sim = nanmedian(spread_g(h_sim(2:end,1)<1));
%%
clearvars -except zz jj string_num meanBY_sim  meanBY_sim_market meanspread_sim y_vec_2sh...
    h_vec_2sh P_x q_g q_g_pf def_pf rel_only_pf prob_choice N_h N_x N_y N_b_g b_g_vec...
    delta mu_r b_g_vec i_b_g_zero

save('climate_persistent_antiguafull.mat')



