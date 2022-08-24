import os
import numpy as np
from .utils import weighted_percentile
import pickle
from .snapshot import Snapshot

# This is a class that compiles the evolution data of a Snapshot/Halo/Disk
# over a specified time for a simulation

class Dust_Evo(object):

	def __init__(self, sdir, snap_lims, cosmological=0, periodic_bound_fix=False,
				 totals=None, medians=None , median_subsamples=None, star_totals=None, dirc='./', name_prefix=''):
		# Set property totals and property medians you want from each snapshot. Also set median masks which will
		# take subsampled medians based on gas properties
		if totals is None:
			self.totals = ['M_gas','M_H2','M_gas_neutral','M_dust','M_metals','M_sil','M_carb',
							'M_SiC','M_iron','M_ORes','M_SNeIa_dust','M_SNeII_dust','M_AGB_dust','M_acc_dust']
		else:
			self.totals = totals
		if medians is None:
			self.medians = ['D/Z','Z','O/H','O/H_gas','dz_acc','dz_SNeIa','dz_SNeII','dz_AGB','dz_sil','dz_carb',
							'dz_SiC','dz_iron','dz_ORes','CinCO','fdense','fH2']
		else:
			self.medians = medians
		if median_subsamples is None:
			self.median_subsamples = ['all','cold','hot','neutral','molecular']
		else:
			self.median_subsamples = median_subsamples
		if star_totals is None:
			self.star_totals = ['M_star','sfr']
		else:
			self.star_totals = star_totals

		self.sdir = sdir
		self.snap_lims = snap_lims
		self.num_snaps = (snap_lims[1]+1)-snap_lims[0]
		self.cosmological = cosmological
		self.dirc = dirc
		# In case the sim was non-cosmological and used periodic BC which causes
		# galaxy to be split between the 4 corners of the box
		self.pb_fix = False
		if periodic_bound_fix and cosmological==0:
			self.pb_fix=True
		# Determines if you want to look at the Snapshot/Halo/Disk
		self.setHalo=False
		self.setDisk=False

		# Get the basename of the directory the snapshots are stored in
		self.basename = os.path.basename(os.path.dirname(os.path.normpath(sdir)))
		# Name for saving object
		self.name = 'dust_evo_'+name_prefix+'_'+self.basename+'_snaps'

		# Check if object file has already been created if so load that first instead of creating a new one
		if os.path.isfile(dirc+self.name):
			with open(dirc+self.name, 'rb') as handle:
				self.dust_evo_data = pickle.load(handle)
			print("Dust_Evo data already exists so loading that first....")
		else:
			self.dust_evo_data = Dust_Evo_Data(sdir, snap_lims, self.totals, self.medians, self.median_subsamples,
							self.star_totals, cosmological=cosmological, pb_fix=periodic_bound_fix,)

		self.k = 0

		return



	# Set data to only include particles in specified halo
	def set_halo(self, **kwargs):
		self.dust_evo_data.set_halo(**kwargs)
		self.setHalo=True

		return


	# Set data to only include particles in specified disk
	def set_disk(self, **kwargs):
		self.dust_evo_data.set_disk(**kwargs)
		self.setDisk=True

		return


	def load(self, increment=5):

		if self.k: return

		# Check if previously saved if so load that and then check if it covers all the snapshots given
		if os.path.isfile(self.dirc+self.name+'.pickle'):
			with open(self.dirc+self.name+'.pickle', 'rb') as handle:
				self.dust_evo_data = pickle.load(handle)
			# If previously saved data set has different snap limits need to update limits before loading
			if not np.array_equiv(self.snap_lims, self.dust_evo_data.snap_lims):
				self.dust_evo_data.change_snap_lims(self.snap_lims)

		while not self.dust_evo_data.all_snaps_loaded:
			self.dust_evo_data.load(increment=increment)
			self.save()

		self.k = 1
		return


	def save(self):

		# First create directory if needed
		if not os.path.isdir(self.dirc):
			os.mkdir(self.dirc)
			print("Directory " + self.dirc +  " Created ")

		with open(self.dirc+self.name+'.pickle', 'wb') as handle:
			pickle.dump(self.dust_evo_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

		return

	# Returns the specified data or derived data field if possible
	def get_data(self, data_name, subsample='all', statistic='median'):

		if statistic not in ['total','median']:
			print("Warning: Statistic must be either total or median.")
			return None

		if not self.dust_evo_data.all_snaps_loaded:
			print("Warning: Not all snapshots have been loaded! All unloaded values will be zero!")

		if data_name in self.totals:
			data = self.dust_evo_data.total_data[data_name]
		elif data_name in self.medians:
			if subsample in self.median_subsamples:
				data = self.dust_evo_data.median_data[subsample][data_name]
			else:
				print('No data for given median subsample available.')
				return None
		elif data_name in self.star_totals:
			data = self.dust_evo_data.star_total_data[data_name]
		elif data_name == 'time':
			data = self.dust_evo_data.time
		elif data_name == 'redshift' and self.dust_evo_data.cosmological:
			data = self.dust_evo_data.redshift
		elif 'source' in data_name:
			if 'total' in statistic:
				if 'source_acc' in data_name:
					data = self.dust_evo_data.total_data['M_acc_dust']/self.dust_evo_data.total_data['M_dust']
				elif 'source_SNeIa' in data_name:
					data = self.dust_evo_data.total_data['M_SNeIa_dust']/self.dust_evo_data.total_data['M_dust']
				elif 'source_SNeII' in data_name:
					data = self.dust_evo_data.total_data['M_SNeII_dust']/self.dust_evo_data.total_data['M_dust']
				elif 'source_AGB' in data_name:
					data = self.dust_evo_data.total_data['M_AGB_dust']/self.dust_evo_data.total_data['M_dust']
				else:
					print(data_name," is not in the dataset.")
					return None
				data[np.isnan(data)] = 0
			elif 'median' in statistic:
				if 'source_acc' in data_name:
					data = self.dust_evo_data.median_data[subsample]['dz_acc']
				elif 'source_SNeIa' in data_name:
					data = self.dust_evo_data.median_data[subsample]['dz_SNeIa']
				elif 'source_SNeII' in data_name:
					data = self.dust_evo_data.median_data[subsample]['dz_SNeII']
				elif 'source_AGB' in data_name:
					data = self.dust_evo_data.median_data[subsample]['dz_AGB']
				else:
					print(data_name," is not in the dataset.")
					return None
			else:
				print(data_name," is not in the dataset.")
				return None
		elif 'spec' in data_name:
			if 'total' in statistic:
				if 'spec_sil' in data_name:
					data = self.dust_evo_data.total_data['M_sil']/self.dust_evo_data.total_data['M_dust']
				elif 'spec_carb' in data_name:
					data = self.dust_evo_data.total_data['M_carb']/self.dust_evo_data.total_data['M_dust']
				elif 'spec_SiC' in data_name:
					data = self.dust_evo_data.total_data['M_SiC']/self.dust_evo_data.total_data['M_dust']
				elif 'spec_iron' in data_name and 'spec_ironIncl' not in data_name:
					data = self.dust_evo_data.total_data['M_iron']/self.dust_evo_data.total_data['M_dust']
				elif 'spec_ORes' in data_name:
					data = self.dust_evo_data.total_data['M_ORes']/self.dust_evo_data.total_data['M_dust']
				else:
					print(data_name," is not in the dataset.")
					return None
				data[np.isnan(data)] = 0
			elif 'median' in statistic:
				if 'spec_sil' in data_name:
					data = self.dust_evo_data.median_data[subsample]['dz_sil']
				elif 'spec_carb' in data_name:
					data = self.dust_evo_data.median_data[subsample]['dz_carb']
				elif 'spec_SiC' in data_name:
					data = self.dust_evo_data.median_data[subsample]['dz_SiC']
				elif 'spec_iron' in data_name and 'spec_ironIncl' not in data_name:
					data = self.dust_evo_data.median_data[subsample]['dz_iron']
				elif 'spec_ORes' in data_name:
					data = self.dust_evo_data.median_data[subsample]['dz_ORes']
				else:
					print(data_name," is not in the dataset.")
					return None
			else:
				print(data_name," is not in the dataset.")
				return None
		else:
			print(data_name," is not in the dataset.")
			return None

		return data.copy()



class Dust_Evo_Data(object):

	def __init__(self, sdir, snap_lims, totals, medians, median_subsamples, star_totals, cosmological=0, pb_fix=False):
		self.sdir = sdir
		self.snap_lims = snap_lims
		self.num_snaps = (snap_lims[1]+1)-snap_lims[0]
		self.snap_loaded = np.zeros(self.num_snaps,dtype=bool)
		self.cosmological = cosmological
		self.time = np.zeros(self.num_snaps)
		if self.cosmological:
			self.redshift = np.zeros(self.num_snaps)


		# In case the sim was non-cosmological and used periodic BC which causes
		# galaxy to be split between the 4 corners of the box
		self.pb_fix = False
		if pb_fix and cosmological==0:
			self.pb_fix=True

		# Populate the data dictionaries
		self.total_data = {key : np.zeros(self.num_snaps) for key in totals}
		self.star_total_data = {key : np.zeros(self.num_snaps) for key in star_totals}
		# Populate the gas property fields corresponding with each mask
		self.median_data = {sub_key : {key : np.zeros(self.num_snaps) for key in medians} for sub_key in median_subsamples}

		self.setHalo=False
		self.setDisk=False
		self.load_kwargs = {}
		self.set_kwargs = {}

		self.all_snaps_loaded=False


		return


	def change_snap_lims(self, snap_lims):
		prepend_snaps = 0
		append_snaps = 0
		if snap_lims[0]<self.snap_lims[0]:
			prepend_snaps = self.snap_lims[0]-snap_lims[0]
			self.snap_lims[0] = snap_lims[0]
		if snap_lims[1]>self.snap_lims[1]:
			append_snaps = snap_lims[1]-self.snap_lims[0]
			self.snap_lims[1] = snap_lims[1]
		self.num_snaps = (snap_lims[1]+1)-snap_lims[0]

		prepend=np.zeros(prepend_snaps); append=np.zeros(append_snaps);
		self.time = np.append(np.concatenate((prepend,self.time)),append)
		if self.cosmological:
			self.redshift = np.append(np.concatenate((prepend,self.redshift)),append)
		self.snap_loaded = np.append(np.concatenate((prepend,self.snap_loaded)),append)

		# Populate the data dictionaries
		for key in self.total_data.keys():
			self.total_data[key] = np.append(np.concatenate((prepend,self.total_data[key])),append)
		for key in self.star_total_data.keys():
			self.star_total_data[key] = np.append(np.concatenate((prepend,self.star_total_data[key])),append)
		# Populate the gas property fields corresponding with each mask
		for sub_key in self.median_data.keys():
			for key in self.median_data[sub_key]:
				self.median_data[sub_key][key] = np.append(np.concatenate((prepend,self.median_data[sub_key][key])),append)

		self.all_snaps_loaded=False


	# Set to include particles in specified halo
	def set_halo(self, load_kwargs={}, set_kwargs={}):
		if not self.setHalo:
			self.setHalo=True
			self.load_kwargs = load_kwargs
			self.set_kwargs = set_kwargs

		return

	# Set to include particles in specified disk
	def set_disk(self, load_kwargs={}, set_kwargs={}):
		if not self.setDisk:
			self.setDisk=True
			self.load_kwargs = load_kwargs
			self.set_kwargs = set_kwargs

		return


	def load(self, increment=5):
		# Load total masses of different gases/stars and then calculated the median and 16/86th percentiles for
		# gas properties for each snapshot. Only loads set increment number of snaps at a time.

		if not self.setHalo and not self.setDisk:
			print("Need to call set_halo() or set_disk() to specify halo/disk to load time evolution data for.")
			return


		snaps_loaded=0
		for i, snum in enumerate(np.arange(self.snap_lims[0],self.snap_lims[1]+1)):


			# Stop loading if already loaded set increment so it can be saved
			if snaps_loaded >= increment:
				return
			# Skip already loaded snaps
			if self.snap_loaded[i]:
				continue

			print('Loading snap',snum,'...')
			sp = Snapshot(self.sdir, snum, cosmological=self.cosmological, periodic_bound_fix=self.pb_fix)
			self.time[i] = sp.time
			if self.cosmological:
				self.redshift[i] = sp.redshift
			# Calculate the data fields for both all particles in the halo and all particles in the disk
			if self.setHalo:
				gal = sp.loadhalo(**self.load_kwargs)
				gal.set_zoom(**self.set_kwargs)
			else:
				gal = sp.loaddisk(**self.load_kwargs)
				gal.set_disk(**self.set_kwargs)

			print('Loading gas data....')
			G = gal.loadpart(0)
			G_mass = G.get_property('M')
			T = G.get_property('T'); nH = G.get_property('nH'); fnh = G.get_property('nh'); fH2 = G.get_property('fH2')
			masks = {}
			for name in self.median_data.keys():
				if name == 'all':
					mask = np.ones(len(G_mass), dtype=bool)
				elif name == 'cold':
					mask = T <= 1E3
				elif name == 'hot':
					mask = T >= 1E4
				elif name == 'neutral':
					mask = fnh > 0.5
				elif name =='molecular':
					mask = fH2*fnh > 0.5
				else:
					print("Median subsampling %s is not supported so assuming all"%name)
					mask = np.ones(len(G_mass), dtype=bool)
				masks[name] = mask


			# First do totals
			for prop in self.total_data.keys():
				prop_mass = G.get_property(prop)
				self.total_data[prop][i] = np.nansum(prop_mass)


			# Now calculate medians for gas properties
			for subsample in self.median_data:
				for prop in self.median_data[subsample].keys():
					prop_vals = G.get_property(prop)
					mask = masks[subsample]
					# Deal with properties that are more than one value
					self.median_data[subsample][prop][i] = weighted_percentile(prop_vals[mask], percentiles=[50],
														weights=G_mass[mask], ignore_invalid=True)


			# Finally do star properties if there are any
			S = gal.loadpart(4)
			print('Loading star data....')
			if S.npart == 0:
				for prop in self.star_total_data.keys():
					self.star_total_data[prop][i] = 0.
			else:
				S_mass = S.get_property('M')
				for prop in self.star_total_data.keys():
					if prop == 'M_star':
						self.star_total_data[prop][i] = np.nansum(S_mass)
					elif prop == 'sfr':
						age = S.get_property('age')
						self.star_total_data[prop][i] = np.nansum(S_mass[age<=10])/1E6 # M_sol/yr

			# snap all loaded
			self.snap_loaded[i]=True
			snaps_loaded+=1

		self.all_snaps_loaded=True
		return