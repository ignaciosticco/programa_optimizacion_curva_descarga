'''
Este script aplica un algoritmo de Differential Evolution para 
hallar los parametros del SFM que mejor ajustan 
la curva de descarga. Los inputs se definen en input_file.py
'''
import pandas as pd 
import os
import random 
import copy
import numpy as np
import input_file as inp
import math

########## Input set (definidos en input_file.py) ##########  
itermax 	= inp.itermax
CP 			= inp.CP 	  		
F 			= inp.F  	  			
epsilon 	= inp.epsilon   
N_agents 	= inp.N_agents
Amin 		= inp.Amin
Amax 		= inp.Amax
Bmin 		= inp.Bmin
Bmax 		= inp.Bmax
knmin 		= inp.knmin
knmax 		= inp.knmax
ktmin 		= inp.ktmin
ktmax 		= inp.ktmax
taumin 		= inp.taumin
taumax 		= inp.taumax
output_name = inp.output_name
#############################################################

def inicializa_agents(Amin,Amax,Bmin,Bmax,knmin,
	knmax,ktmin,ktmax,taumin,taumax,N_agents):
	'''
	Crea la poblacion inicial de agentes
	Cada agente es un vector de parametros
	'''
	initial_population = []
	
	for i in range(0,N_agents):
		tau = round(random.uniform(taumin,taumax),2)
		A = round(random.uniform(Amin,Amax),2)
		B = round(random.uniform(Bmin,Bmax),2)
		kn = round(random.uniform(knmin,knmax),2)
		kt = round(random.uniform(ktmin,ktmax),2) 
		# Pared e individuos con igual friccion; no optimizo kt_wall
		kt_wall = kt  
		initial_population+=[[tau,A,B,kn,kt]]
	
	return initial_population

def calcula_discharge_inicial(list_agents):
	'''
	Crea una lista donde cada elemento es 
	el la curva de descarga (solo cantidad promedio de individuos que entraron - medido de 0s a 40s con paso 2s-). Esto es solo para los agentes de la poblacion inicial
	'''
	list_discharge = []
	list_discharge_std = []
	for agent in list_agents:
		output_file_parameters(agent)
		os.system("rm raw_discharge.txt")
		os.system("./run")
		result = calcula_mean_discharge()
		list_discharge += [result[0]]
		list_discharge_std += [result[1]]
	return list_discharge,list_discharge_std
		


def crea_agente(list_agents,agent_old,CP,F):
	'''
	Crea un nuevo agente a partir del algoritmo de 
	Differential Evolution. 
	'''
	agent_a,agent_b,agent_c = select_agents(list_agents,agent_old)
	agent_new = [0]*len(agent_old)
	for i in range(0,len(agent_old)):
		random_number = random.random()
		if random_number < CP:
			
			new_tmp = round(agent_a[i] + F*(agent_b[i]-agent_c[i]),2)
			if new_tmp < 0:
				# Warning: puse un abs (distinto del original)
				# Con esto evito parametros negativos
				agent_new[i] = round(agent_a[i] + F*abs(agent_b[i]-agent_c[i]),2)
			else:
				agent_new[i] = new_tmp

		else:
			agent_new[i] = agent_old[i]

	return agent_new

def select_agents(list_agents,agent_old):
	'''
	Selects 3 agents different from agent_old
	'''
	list_agents_copy = copy.copy(list_agents)
	list_agents_copy.remove(agent_old)

	agent_a = random.choice(list_agents_copy)
	list_agents_copy.remove(agent_a)

	agent_b = random.choice(list_agents_copy)
	list_agents_copy.remove(agent_b)

	agent_c = random.choice(list_agents_copy)
	list_agents_copy.remove(agent_c)

	return agent_a,agent_b,agent_c


def output_file_parameters(agent_new):
	'''
	Imprime el archivo de parametros que luego usa LAMMPS para
	correr la simulacion
	'''
	with open('parameters_sfm.txt', 'w') as f:
		for item in agent_new:
			f.write("%s\n" % item)
		f.write("%s\n" % agent_new[-1])
	f.close()

def calcula_mean_discharge():
	'''
	Calcula el valor medio y std de la curva de descarga
	Toma el archivo que sale de la simulacion: raw_discharge.txt
	'''
	os.system("rm mean_discharge.txt")
	os.system("python3 procesa_descarga_2.0.py")

	data = pd.read_csv("mean_discharge.txt", delimiter='\t')
	mean_discharge = data["0.mean_time"].tolist()
	std_discharge = data["1.std_time"].tolist()
	return mean_discharge,std_discharge


def evalua_new_agent(list_agents,list_discharge,mean_discharge_new,agent_new,idx_agent,agent_record,discharge_record,discharge_empirical):
	'''
	Reemplaza el nuevo agente por el viejo 
	si el nuevo tiene mejor performance que el viejo
	'''

	delta_t_new = calcula_delta(mean_discharge_new,discharge_empirical)
	delta_t_old = calcula_delta(list_discharge[idx_agent],discharge_empirical)

	if delta_t_new < delta_t_old :
		list_agents[idx_agent] = agent_new
		list_discharge[idx_agent] = mean_discharge_new

	return


def record(idx_agent,idx_agent_record,iteracion,iteracion_record,agent_new,mean_discharge_new,std_discharge_new,agent_record,discharge_record,std_discharge_record,delta_record,delta_t):
	'''
	Registra agentes nuevos con su respectiva curva de descarga, error, indice e iteracion a la cual corresponde. Todos los agentes son registrados (sean mejores que sus predecesores o no)
	'''
	idx_agent_record+=[idx_agent]
	iteracion_record+=[iteracion]
	agent_record += [agent_new]
	discharge_record += [mean_discharge_new]
	std_discharge_record +=[std_discharge_new]
	delta_record += [delta_t]

	return agent_record,discharge_record,std_discharge_record,delta_record,idx_agent_record,iteracion_record

def output_record(agent_record,discharge_record,std_discharge_record,delta_record,output_name,idx_agent_record,iteracion_record):
	'''
	Imprime archivo txt con curva de descarga y los set de parametros registrados
	'''	
	tau = [item[0] for item in agent_record]
	A = [item[1] for item in agent_record]
	B = [item[2] for item in agent_record]
	kn= [item[3] for item in agent_record]
	kt= [item[4] for item in agent_record]
	kt_wall= [item[4] for item in agent_record]

	
	df = pd.DataFrame({'0. Error':np.array(delta_record).astype(int),'1. Agent':np.array(idx_agent_record).astype(int),'2. Iteracion':np.array(iteracion_record).astype(int),'3. Discharge':discharge_record,'4. Std Discharge':std_discharge_record,'A':A,'B':B,'tau':tau,'kn':kn,'kt':kt,'kt_wall':kt_wall})

	df.to_csv('{}.txt'.format(output_name), index = False,sep='\t')
	
	return df

def load_discharge_empirical():
	data_empirical = pd.read_csv("discharge_empirical.txt",sep="\t")
	time_empirical = data_empirical["0.time"].to_list()
	return time_empirical

def imprime_estado(iteracion):
	'''
	Imprime el estado del programa, lo que registra el estado es la iteracion actual
	'''
	with open('estado.txt', 'a') as f:
		f.write("%s\n" % iteracion)
	f.close()


def calcula_delta(discharge_simulated,discharge_empirical):
	'''
	Calcula la diferencia de tiempos entre la curva empirica y la simulada
	'''

	residuos = np.array(discharge_simulated)-np.array(discharge_empirical)
	delta_t = np.sum(np.abs(residuos))
	return delta_t

def record_inicial(idx_agent_record,iteracion,iteracion_record,list_agents,list_discharge,std_list_discharge,agent_record,discharge_record,std_discharge_record,delta_record,discharge_empirical):
	'''
	Registra los agentes iniciales (indice, parametros, descarga y delta)
	'''
	for i in range(0,len(list_agents)):

		idx_agent_record+=[i]
		iteracion_record+=[0]
		agent_record += [list_agents[i]]
		discharge_record += [list_discharge[i]]
		std_discharge_record +=[std_list_discharge[i]]
		delta_record += [calcula_delta(list_discharge[i],discharge_empirical)]

	return agent_record,discharge_record,std_discharge_record,delta_record,idx_agent_record,iteracion_record


def main():

	####################### Inicializacion #######################
	discharge_empirical = load_discharge_empirical()
	list_agents = inicializa_agents(Amin,Amax,Bmin,Bmax,knmin,knmax,
		ktmin,ktmax,taumin,taumax,N_agents)
	result_inicial = calcula_discharge_inicial(list_agents)
	list_discharge = result_inicial[0]
	std_list_discharge = result_inicial[1]
	agent_record = []
	discharge_record = []
	std_discharge_record = []
	delta_record = []
	idx_agent_record = []
	iteracion_record = []
	iteracion = 0
	flag = True
	record_inicial(idx_agent_record,iteracion,iteracion_record,list_agents,list_discharge,std_list_discharge,agent_record,discharge_record,std_discharge_record,delta_record,discharge_empirical)
	iteracion = 1
	##############################################################
	os.system("rm estado.txt")
	while iteracion < itermax+1 and flag:
		imprime_estado(iteracion)
		for idx_agent in range(0,len(list_agents)):
			agent_old = list_agents[idx_agent]
			agent_new = crea_agente(list_agents,agent_old,CP,F) 
			if agent_new != agent_old: 
				# crea txt con parametros para la simulacion
				output_file_parameters(agent_new) 
				os.system("rm raw_discharge.txt")
				os.system("./run")
				result_mean_discharge = calcula_mean_discharge()
				mean_discharge_new = result_mean_discharge[0]
				std_discharge_new = result_mean_discharge[1]

				evalua_new_agent(list_agents,list_discharge,mean_discharge_new,agent_new,idx_agent,
					agent_record,discharge_record,discharge_empirical)	
				delta_t = calcula_delta(mean_discharge_new,discharge_empirical)
				if delta_t<epsilon:
					flag = False						
				record(idx_agent,idx_agent_record,iteracion,iteracion_record,agent_new,mean_discharge_new,std_discharge_new,agent_record,discharge_record,std_discharge_record
					,delta_record,delta_t)
		iteracion+=1
	
	output_record(agent_record,discharge_record,std_discharge_record,delta_record,output_name,idx_agent_record,iteracion_record)

if __name__=='__main__':
     main()
