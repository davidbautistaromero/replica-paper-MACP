function m = nanmedian(x, dim)
%NANMEDIAN Shim de compatibilidad para el codigo de Mallucci (2022).
%   Ver nanmean.m. nanmedian(x) == median(x,'omitnan').
if nargin < 2
    m = median(x, 'omitnan');
else
    m = median(x, dim, 'omitnan');
end
end
