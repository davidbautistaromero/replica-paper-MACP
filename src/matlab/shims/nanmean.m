function m = nanmean(x, dim)
%NANMEAN Shim de compatibilidad para el codigo de Mallucci (2022).
%   nanmean/nanmedian venian del Statistics and Machine Learning Toolbox y ya no
%   estan disponibles en MATLAB base. Estas funciones reproducen su semantica con
%   la sintaxis moderna ('omitnan'), sin tocar el codigo del autor: MATLAB
%   resuelve primero las funciones del directorio de trabajo.
%
%   Equivalencias: nanmean(x) == mean(x,'omitnan');  nanmean(x,d) == mean(x,d,'omitnan').
if nargin < 2
    m = mean(x, 'omitnan');
else
    m = mean(x, dim, 'omitnan');
end
end
