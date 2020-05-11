'''
Toma un archivo de curva de descarga y devuelve un grafico de la descarga promedio y un archivo con los datos promediados
El archivo de ingreso tiene 3 columnas: time (sampleado cada 0.05 s), Cantidad de peatones que estan afuera y el numero de iteracion
'''


import pylab
import numpy as np
import math
import pandas as pd

# a dos columnas: 3+3/8 (ancho, in)
# a una columna : 6.5   (ancho  in)

golden_mean = (math.sqrt(5)-1.0)/2.0        # Aesthetic ratio
fig_width = 3+3/8 			    # width  in inches
fig_height = fig_width*golden_mean          # height in inches
fig_size =  [fig_width,fig_height]

params = {'backend': 'ps',
          'axes.titlesize': 8,
          'axes.labelsize': 9,
          'axes.linewidth': 0.5, 
          'axes.grid': True,
          'axes.labelweight': 'normal',  
          'font.family': 'serif',
          'font.size': 8.0,
          'font.weight': 'normal',
          'text.color': 'black',
          'xtick.labelsize': 8,
          'ytick.labelsize': 8,
          'text.usetex': True,
          'legend.fontsize': 8,
          'figure.dpi': 300,
          'figure.figsize': fig_size,
          'savefig.dpi': 300,
         }

pylab.rcParams.update(params)


def promedia_group_time(df):
     '''
     Promedia la cantidad de peatones que esta afuera habiendo agrupado por valores de tiempo (a todos las filas con t = ti les calcula el promedio de la cantidad de individuos afuera, hace eso para todo i)
     '''

     # selecciona aquellas filas cuyo t es multiplo de 2
     df_multip2 = df.loc[(df['time'] % 2==0)] 
     mean = df_multip2.groupby('time').mean()["pedestrians_outside"].tolist()
     std = df_multip2.groupby('time').std()["pedestrians_outside"].tolist()

     return mean,std


def promedia_group_N(df,n_bins):
     '''
     Promedia los tiempos habiendo agrupado por la cantidad de peatones que estan afuera del recinto (a todas las filas con Ni-1<Ni<Ni+1 les calcula el promedio del tiempo en el que estan)
     '''

     mean_entered_grouped =df.groupby(pd.cut(df["pedestrians_outside"], n_bins))["time"].mean().values.tolist()
     std_time_grouped =df.groupby(pd.cut(df["pedestrians_outside"], n_bins))["time"].std().values.tolist()
     return mean_entered_grouped,std_time_grouped

def corrije_largo(mean_entered,std_entered,time):
     '''
     Agrega elementos a la lista (mean_entered y std_entered).
     Esto sirve cuando todos los peatones entran antes del tiempo empirico.
     Completamos la lista diciendo que para t >tf num_entered (t) = 268
     268 es el maximo numero de peatones que entro (medicion empirica)
     '''

     longitud = len(mean_entered)
     total_len = len(time)
     mean_entered = mean_entered+(total_len-longitud)*[268]
     std_entered = std_entered+(total_len-longitud)*[0]

     return mean_entered,std_entered

def main():

     ## PARAMETERS ##
     Ntotal = 303 # Cantidad de individuos total (entran + no entran)
     Nfinal = 35  # Cantidada de individuos que no entran al local
     step_n = 10
     output_name = 'mean_discharge'
     vd = 5
     time = np.arange(2,42,2)
     ################
     file_name = 'raw_discharge.txt'.format(vd)
     df = pd.read_csv(file_name, sep=" ", header=None)
     df.columns = ["time", "pedestrians_outside", "iter"]
     df_selected_times = df.loc[df['time'].isin(time)]
     mean_ped_outside = df.groupby(df_selected_times["time"])["pedestrians_outside"].mean().values.tolist()
     mean_entered = [Ntotal - x for x in mean_ped_outside]
     std_entered = df.groupby(df_selected_times["time"])["pedestrians_outside"].std().values.tolist()
     result_correction = corrije_largo(mean_entered,std_entered,time)
     mean_entered = result_correction[0]
     std_entered = result_correction[1]

     # To do: poner std de las mediciones 
     time = np.insert(time, 0,0)
     mean_entered = [0]+mean_entered
     std_entered = [0]+std_entered  

     dfout = pd.DataFrame({'0.time': time,'1.mean_ped_inside_simulated':np.round(mean_entered,1),'2.std_ped_inside_simulated':np.round(std_entered,1)})
     dfout.to_csv('{}.txt'.format(output_name), index=False,sep='\t')


if __name__=='__main__':
     main()

