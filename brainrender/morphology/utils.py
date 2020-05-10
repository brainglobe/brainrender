from brainrender import DEFAULT_NEURITE_RADIUS

from morphapi.morphology.morphology import Neuron

from vtkplotter import merge


def get_neuron_actors_with_morphapi(swcfile=None, neuron=None):
	if swcfile is None and neuron is None:
		raise ValueError('No input passed')

	if swcfile is not None:
		neuron = Neuron(swc_file=neuron)
	
	neurites, whole_neuron = neuron.create_mesh(neurite_radius=DEFAULT_NEURITE_RADIUS)

	actors = dict(
		soma=neurites['soma'],
		axon = neurites['axon'],
		dendrites = merge(neurites['basal_dendrites'], neurites['apical_dendrites'])
	)

	return actors, whole_neuron



def edit_neurons(neurons, **kwargs):
	"""
		Modify neurons actors after they have been created, at render time.
		neurons should be a list of dictionaries with soma, dendrite and axon actors of each neuron.
	:param neurons: list of dictionaries with vtk actors for each neuron
	:param **kwargs: 
	"""
	if not isinstance(neurons, (list, tuple)):
		neurons = [neurons]

	soma_color, axon_color, dendrites_color = None, None, None
	for neuron in neurons:
		if "random_color" in kwargs:
			if kwargs["random_color"]:
				if not isinstance(kwargs["random_color"], str):
					color = get_random_colors(n_colors=1)
				else: # random_color is a colormap 
					color = colorMap(np.random.randint(1000), name=kwargs["random_color"], vmin=0, vmax=1000)
				axon_color = soma_color = dendrites_color = color
		elif "color_neurites" in kwargs:
			soma_color = neuron["soma"].color()
			if not kwargs["color_neurites"]:
				axon_color = dendrites_color = soma_color
			else:
				if not "axon_color" in kwargs:
					# print("no axon color provided, using somacolor")
					axon_color = soma_color
				else:
					axon_color = kwargs["axon_color"]

				if not "dendrites_color" in kwargs:
					# print("no dendrites color provided, using somacolor")
					dendrites_color = soma_color
				else:
					dendrites_color = kwargs["dendrites_color"]
		elif "soma_color" in kwargs:
			if check_colors(kwargs["soma_color"]):
				soma_color = kwargs["soma_color"]
			else: 
				print("Invalid soma color provided")
				soma_color = neuron["soma"].color()
		elif "axon_color" in kwargs:
			if check_colors(kwargs["axon_color"]):
				axon_color = kwargs["axon_color"]
			else: 
				print("Invalid axon color provided")
				axon_color = neuron["axon"].color()
		elif "dendrites_color" in kwargs:
			if check_colors(kwargs["dendrites_color"]):
				dendrites_color = kwargs["dendrites_color"]
			else: 
				print("Invalid dendrites color provided")
				dendrites_color = neuron["dendrites"].color()

		if soma_color is not None: 
			neuron["soma"].color(soma_color)
		if axon_color is not None: 
			neuron["axon"].color(axon_color)
		if dendrites_color is not None: 
			neuron["dendrites"].color(dendrites_color)


		if "mirror" in kwargs:
			if "mirror_coord" in kwargs:
				mcoord = kwargs["mirror_coord"]
			else:
				raise ValueError("Need to pass the mirror point coordinate")
			
			# mirror X positoin
			for name, actor in neuron.items():
				if "only_soma" in kwargs:
					if kwargs["only_soma"] and name != "soma": continue
					
				# get mesh points coords and shift them to other hemisphere
				if isinstance(actor, list):
					continue
				coords = actor.points()
				shifted_coords = [[c[0], c[1], mcoord + (mcoord-c[2])] for c in coords]
				actor.points(shifted_coords)
			
				neuron[name] = actor.mirror(axis='n')

	return neurons