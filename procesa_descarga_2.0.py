'''
Toma un archivo de curva de descarga y devuelve un archivo con los datos promediados
El archivo de ingreso tiene 3 columnas: time (sampleado cada 0.05 s), Cantidad de peatones que estan afuera y el numero de iteracion. 
El archivo de salida tiene 3 columnas: Tiempo promedio, el desvio standard del tiempo y la cantidad de peatones (esta ultima columna es la cantidad de peatones que ingresaron al local y corresponde a la data empirica)
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


def rellena(mean_time,std_time,entered_empirical,df):
     '''
     Rellena con el valor anterior a aquellos valores de "cantidad de personas ingresadas" que no estan en la simulacion pero si estan en la data empirica. Este relleno sirve solo cuando hay muy poca estadistica. 
     Warning: Rellenar con el tiempo anterior es una eleccion arbitraria de diseno. Se esta cometiendo un error pero ese error es chico y solamente se comete cuando hay poca estadistica
     '''

     df_selected_entered = df.loc[df['pedestrians_inside'].isin(entered_empirical)]
     empir_in_sim = df.groupby(df_selected_entered["pedestrians_inside"])["pedestrians_inside"].mean().values.tolist()
     mean_time_out = [0.0]*len(entered_empirical)
     std_time_out = [0.0]*len(entered_empirical)

     j = 0
     for i in range(0,len(entered_empirical)):
          if entered_empirical[i] in empir_in_sim:
               mean_time_out[i] = mean_time[j]
               std_time_out[i] = std_time[j]
               j+=1
          else:
               mean_time_out[i] = mean_time_out[i-1]
               std_time_out[i] = std_time_out[i-1]
          

     return mean_time_out,std_time_out

def main():

     ## PARAMETERS ##
     Ntotal = 303 # Cantidad de individuos total (entran + no entran)
     Nfinal = 35  # Cantidada de individuos que no entran al local
     step_n = 10
     output_name = 'mean_discharge'
     vd = 5
     entered_empirical = [0,16,33,47,63,76,90,103,114,131,146,162,176,186,200,213,224,232,246,255,268]
     ################
     file_name = 'raw_discharge.txt'.format(vd)
     df = pd.read_csv(file_name, sep=" ", header=None)
     df.columns = ["time", "pedestrians_outside", "iter"]
     df["pedestrians_outside"]=Ntotal-df["pedestrians_outside"]
     df.columns = ["time", "pedestrians_inside", "iter"]
     df_selected_entered = df.loc[df['pedestrians_inside'].isin(entered_empirical)]

     mean_time = df.groupby(df_selected_entered["pedestrians_inside"])["time"].mean().values.tolist()
     std_time = df.groupby(df_selected_entered["pedestrians_inside"])["time"].std().values.tolist()
     mean_time,std_time = rellena(mean_time,std_time,entered_empirical,df)
     dfout = pd.DataFrame({'0.mean_time': np.round(mean_time,1),'1.std_time':np.round(std_time,1),'2.ped_inside_simulated':np.round(entered_empirical,1)})

     dfout.to_csv('{}.txt'.format(output_name), index=False,sep='\t')


if __name__=='__main__':
     main()

