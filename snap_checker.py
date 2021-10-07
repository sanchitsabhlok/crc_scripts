import os
import subprocess
from gizmo_library.time_evolution import Dust_Evo
from gizmo import *
from dust_plots import *
import gizmo_library.config as config

# Directory of snap file
snap_dirs = ['/oasis/tscc/scratch/cchoban/non_cosmo/Species/nano_Fe/output/','/oasis/tscc/scratch/cchoban/new_gizmo/FIRE-2/output/',
				'/oasis/tscc/scratch/cchoban/new_gizmo/FIRE-3_cool/output','/oasis/tscc/scratch/cchoban/new_gizmo/FIRE-3/output']
# Snapshots to check
snaps = [110,150]

cosmological = False
pb_fix=True
dust_depl=False

# Label for test plots
labels = ['FIRE-2 Old', 'FIRE-2 New','FIRE-3 New Cool', 'FIRE-3 Old Cool']


# Maximum radius, disk, height, and disk orientation used for getting data
r_max = 20 # kpc
disk_height = 2 # kpc


for snap_num in snaps:
	galaxies = []
	for j,snap_dir in enumerate(snap_dirs):
		print("Snap Dirc: ",snap_dir)
		print("Snap Num:",snap_num)
		galaxy = load_disk(snap_dir, snap_num, cosmological=cosmological, id=-1, mode='AHF', hdir=None, periodic_bound_fix=pb_fix, rmax=r_max, height=disk_height)
		galaxies += [galaxy]

		print("NumParts:", galaxy.sp.npart)
		print("Dust Implementation:", galaxy.sp.dust_impl)
		print("Number of Metal Elements:",galaxy.sp.Flag_Metals)
		print("Number of Dust Elements:",galaxy.sp.Flag_DustMetals)
		print("Number of Dust Species:",galaxy.sp.Flag_DustSpecies)

		flag_species = 0
		if galaxy.sp.dust_impl=='species':
			flag_species = 1


		G = galaxy.loadpart(0)
		nH = G.rho*config.UnitDensity_in_cgs * ( 1. - (G.z[:,0]+G.z[:,1])) / config.H_MASS

		print("Making simple phase plot and projection to check by eye...\n")
		config.PROP_INFO['nH'][1]=[1.1E-3, 0.9E3] # Increase the density range
		config.PROP_INFO['T'][1]=[1.1E1, 2E6] # Increase the temp range
		binned_phase_plot('M_gas', [galaxy], bin_nums=200, labels=None, color_map='plasma', foutname=labels[j]+"_phase_plot_"+str(snap_num)+".png")
		binned_phase_plot('D/Z', [galaxy], bin_nums=200, labels=None, color_map='magma', foutname=labels[j]+"_DZ_phase_plot_"+str(snap_num)+".png")
		#config.PROP_INFO['nH'][1]=[1.1E-2, 0.9E3]
		#config.PROP_INFO['T'][1]=[1.1E1, 0.9E5]



		config.PROP_INFO['sigma_dust'][1]=[1E-2,1E0]
		snap_projection(['sigma_dust','sigma_carb','sigma_sil','sigma_iron','sigma_ORes'],galaxy, L=r_max, Lz=disk_height, pixel_res=0.1,
						color_map=['magma','inferno','inferno','inferno','inferno','inferno'], labels=['Dust','Carbonaceous','Silicates','Iron','O-res'],
						foutname=labels[j]+'_snap_'+str(snap_num)+'_dust_projection.png')
		config.PROP_INFO['sigma_dust'][1]=[1E-3,1E0]

		print("########################################\n")

		print("Checking for Nans...")
		nan_ind = np.argwhere(np.isnan(G.dz[:,0]))
		if len(nan_ind) > 0:
			print("%i particles with NaNs detected"%len(nan_ind))
			nan_ind = np.argwhere(np.isnan(G.dz[:,0]))
			print("Dust Metals:",G.dz[nan_ind])
			if flag_species:
				print("Species:",G.spec[nan_ind])
			print("Sources:",G.dzs[nan_ind])
			print("nH:", nH[nan_ind])
			print("T:", G.T[nan_ind])

		print("########################################\n")

		print("Checking for negative numbers...\n")
		neg_ind = np.argwhere(np.logical_and(np.any(G.dz<0,axis=1),np.any(G.dzs<0,axis=1),np.any(G.spec<0,axis=1)))
		if len(neg_ind) > 0:
			print("%i particles with negative numbers detected"%len(neg_ind))
			print("Dust Metals:",G.dz[neg_ind])
			if flag_species:
				print("Species:",G.spec[neg_ind])
			print("Sources:",G.dzs[neg_ind])
			print("nH:", nH[neg_ind])
			print("T:", G.T[neg_ind])


		print("########################################\n")

		print("Checking for too much dust...\n")
		over_ind = np.argwhere(np.any(G.dz>G.z[:,:11],axis=1)).flatten()
		if len(over_ind) > 0:
			print("%i particles with too much dust detected"%len(over_ind))
			print("Metals:",G.z[over_ind])
			print("D/Z:",G.dz[over_ind]/G.z[over_ind,:11])
			if flag_species:
				print("Species:",G.spec[over_ind])
			print("Sources:",G.dzs[over_ind])
			print("nH:", nH[over_ind])
			print("T:", G.T[over_ind])
			print("\t fH2:",G.fH2[over_ind])
			print("\t fMC:",G.fMC[over_ind])
			print("\t CinCO:",G.CinCO[over_ind]/G.z[over_ind,2],"\n")

		print("########################################\n")

		print("Checking dust source fractions add up to one...\n")
		over_ind = np.abs(np.sum(G.dzs,axis=1)-1)>1E-3
		if len(G.dzs[over_ind]) > 0:
			print("%i particles with dust source fractions not adding up"%len(over_ind))
			print("Metals:",G.z[over_ind])
			print("D/Z:",G.dz[over_ind]/G.z[over_ind,:11])
			if flag_species:
				print("Species:",G.spec[over_ind])
			print("Sources:",G.dzs[over_ind])
			print("nH:", nH[over_ind])
			print("T:", G.T[over_ind])
			print("\t fH2:",G.fH2[over_ind])
			print("\t fMC:",G.fMC[over_ind])
			print("\t CinCO:",G.CinCO[over_ind]/G.z[over_ind,2],"\n")

		if flag_species:

			print("########################################\n")

			print("Checking dust metals and dust species add up...\n")
			# Maximum allowed error between species and dust metals
			abs_error = 1E-2
			# Add up the elements from each dust species
			dust_metals = np.zeros(np.shape(G.dz))
			sil_num_atoms = [3.631,1.06,1.,0.571] # O, Mg, Si, Fe
			sil_elems_index = [4,6,7,10] # O,Mg,Si,Fe 
			dust_formula_mass = 0

			if galaxy.sp.Flag_DustSpecies==4:
				# Silicates
				for k in range(len(sil_num_atoms)):
					dust_formula_mass += sil_num_atoms[k] * config.ATOMIC_MASS[sil_elems_index[k]]
				for k in range(len(sil_num_atoms)):
					dust_metals[:,sil_elems_index[k]] += G.spec[:,0] * sil_num_atoms[k] * config.ATOMIC_MASS[sil_elems_index[k]] / dust_formula_mass
				# Carbon
				dust_metals[:,2] += G.spec[:,1]
				# Silicon Carbide
				dust_formula_mass = config.ATOMIC_MASS[2] + config.ATOMIC_MASS[7]
				dust_metals[:,2] += G.spec[:,2] * config.ATOMIC_MASS[2] / dust_formula_mass
				dust_metals[:,7] += G.spec[:,2] * config.ATOMIC_MASS[7] / dust_formula_mass
				# Iron
				dust_metals[:,10] += G.spec[:,3]
			
			elif galaxy.sp.Flag_DustSpecies==5:
				# Silicates
				for k in range(len(sil_num_atoms)):
					dust_formula_mass += sil_num_atoms[k] * config.ATOMIC_MASS[sil_elems_index[k]]
				for k in range(len(sil_num_atoms)):
					dust_metals[:,sil_elems_index[k]] += G.spec[:,0] * sil_num_atoms[k] * config.ATOMIC_MASS[sil_elems_index[k]] / dust_formula_mass
				# Carbon
				dust_metals[:,2] += G.spec[:,1]
				# Silicon Carbide
				dust_formula_mass = config.ATOMIC_MASS[2] + config.ATOMIC_MASS[7]
				dust_metals[:,2] += G.spec[:,2] * config.ATOMIC_MASS[2] / dust_formula_mass
				dust_metals[:,7] += G.spec[:,2] * config.ATOMIC_MASS[7] / dust_formula_mass
				# Iron
				dust_metals[:,10] += G.spec[:,3]
				# Oxygen Reservoir
				dust_metals[:,4] += G.spec[:,4]

			elif galaxy.sp.Flag_DustSpecies==6:
				# Iron in silicates comes in the form of a seperate dust species 'iron inclusions'
				sil_num_atoms = [3.631,1.06,1.] # O, Mg, Si, Fe
				sil_elems_index = [4,6,7] # O,Mg,Si,Fe
				# Silicates
				for k in range(len(sil_num_atoms)):
					dust_formula_mass += sil_num_atoms[k] * config.ATOMIC_MASS[sil_elems_index[k]]
				for k in range(len(sil_num_atoms)):
					dust_metals[:,sil_elems_index[k]] += G.spec[:,0] * sil_num_atoms[k] * config.ATOMIC_MASS[sil_elems_index[k]] / dust_formula_mass
				# Carbon
				dust_metals[:,2] += G.spec[:,1]
				# Silicon Carbide
				dust_formula_mass = config.ATOMIC_MASS[2] + config.ATOMIC_MASS[7]
				dust_metals[:,2] += G.spec[:,2] * config.ATOMIC_MASS[2] / dust_formula_mass
				dust_metals[:,7] += G.spec[:,2] * config.ATOMIC_MASS[7] / dust_formula_mass
				# Free-Flying Iron and Iron Inclusions
				dust_metals[:,10] += G.spec[:,3] + G.spec[:,5]
				# Oxygen Reservoir
				dust_metals[:,4] += G.spec[:,4]
			
			else:
				print("\t Number of dust species not supported for this check:",galaxy.sp.Flag_DustSpecies)

			dust_metals[:,0]=np.sum(dust_metals[:,2:],axis=1)
			bad_ind = np.argwhere(np.logical_and(np.any(~np.isclose(G.dz, dust_metals, rtol=abs_error, atol=0,equal_nan=True),axis=1),G.dz[:,0]/G.z[:,0]>0.01)).flatten()

			if len(bad_ind) > 0:
				bad_ind = bad_ind[:5]
				print("%i particles with D/Z>0.01 and element and species not matching by %f%% "%(len(bad_ind),abs_error*100))
				print("Dust Metals:",G.dz[bad_ind])
				print("Dust Metals from Species:",dust_metals[bad_ind])
				print("D/Z:",G.dz[bad_ind]/G.z[bad_ind,:11])
				print("Species:",G.spec[bad_ind])
				print("Sources:",G.dzs[bad_ind])
				print("nH:", nH[bad_ind])
				print("T:", G.T[bad_ind])
				print("\t fH2:",G.fH2[bad_ind])
				print("\t fMC:",G.fMC[bad_ind])
				print("\t CinCO:",G.CinCO[bad_ind]/G.z[bad_ind,2],"\n")
				print("\t Sum of Species::",np.sum(G.spec[bad_ind],axis=1))
				print("\t Sum of Elements:",np.sum(G.dz[bad_ind,2:],axis=1))
				print("\t Total Dust:",G.dz[bad_ind,0])


		print("########################################\n")

		print("Sanity Checks...\n")

		print("Particle with Max Dust Mass...")
		max_ind = np.nanargmax(G.dz[:,0])
		print("\t D/Z:",G.dz[max_ind]/G.z[max_ind,:11])
		print("\t Dust Metals:",G.dz[max_ind])
		print("\t Metals:",G.z[max_ind])
		if flag_species:
				print("\t Species:",G.spec[max_ind])
		print("\t Sources:",G.dzs[max_ind])
		print("\t nH:", nH[max_ind])
		print("\t T:", G.T[max_ind])
		if flag_species:
			print("\t Sum of Species: %e \t Sum of Elements: %e Total Dust: %e\n"%(np.sum(G.spec[max_ind]),np.sum(G.dz[max_ind,2:]),G.dz[max_ind,0]))
		else:
			print("\t Sum of Elements: %e Total Dust: %e\n"%(np.sum(G.dz[max_ind,2:]),G.dz[max_ind,0]))
		print("\t fH2: %e \t fMC: %e \t CinCO: %e \n"%(G.fH2[max_ind],G.fMC[max_ind],G.CinCO[max_ind]/G.z[max_ind,2]))


		if flag_species and galaxy.sp.Flag_DustSpecies>4:
			print("Particle with Max O Reservoir...")
			max_ind = np.nanargmax(G.spec[:,4])
			print("\t D/Z:",G.dz[max_ind]/G.z[max_ind,:11])
			print("\t Dust Metals:",G.dz[max_ind])
			print("\t Metals:",G.z[max_ind])
			print("\t Species:",G.spec[max_ind])
			print("\t Sources:",G.dzs[max_ind])
			print("\t nH:", nH[max_ind])
			print("\t T:", G.T[max_ind])
			print("\t Sum of Species: %e \t Sum of Elements: %e Total Dust: %e\n"%(np.sum(G.spec[max_ind]),np.sum(G.dz[max_ind,2:]),G.dz[max_ind,0]))
			print("\t fH2: %e \t fMC: %e \t CinCO: %e \n"%(G.fH2[max_ind],G.fMC[max_ind],G.CinCO[max_ind]/G.z[max_ind,2]))

		



	print("Creating dust plots to check by eye...")

	binned_phase_plot('M_gas', galaxies, bin_nums=150, labels=labels, color_map='plasma', foutname="compare_phase_plot_"+str(snap_num)+".png")
	binned_phase_plot('D/Z', galaxies, bin_nums=150, labels=labels, color_map='magma', foutname="compare_DZ_phase_plot_"+str(snap_num)+".png")

	dmol_vs_props(['fH2','fMC'], ['nH', 'T'], galaxies, bin_nums=50, labels=labels, foutname='check_snap_'+str(snap_num)+'_fH2_and_fMC_vs_nH_T.png', std_bars=True)

	dmol_vs_props(['CinCO'], ['nH', 'T'], galaxies, bin_nums=50, labels=labels, foutname='check_snap_'+str(snap_num)+'_CinCO_vs_nH_T.png', std_bars=True)

	plot_prop_vs_prop(['nH'], ['D/Z'], galaxies, bin_nums=40, labels=labels, foutname='check_snap_'+str(snap_num)+'_DZ_vs_nH.png', std_bars=True, style='color', include_obs=True)

	elems = ['Mg','Si','Fe','O','C']
	plot_elem_depletion_vs_prop(elems, 'nH', galaxies, bin_nums=50, labels=labels, foutname='check_snap_'+str(snap_num)+'_obs_elemental_dep_vs_dens.png', \
						std_bars=True, style='color', include_obs=True)

	plot_obs_prop_vs_prop(['sigma_gas','r'], ['D/Z','D/Z'], galaxies, pixel_res=2, bin_nums=40, labels=labels, foutname='compare_B13_obs_DZ_vs_surf_'+str(snap_num)+'.png', \
						std_bars=True, style='color', include_obs=True)


