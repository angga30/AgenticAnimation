extends Node3D

var config_data: Dictionary

func _ready() -> void:
	print("Godot: Initializing SceneBuilder...")
	var file_path = "res://contract.json"
	if not FileAccess.file_exists(file_path):
		printerr("Godot: contract.json not found!")
		get_tree().quit(1)
		return

	var file = FileAccess.open(file_path, FileAccess.READ)
	var json = JSON.new()
	var err = json.parse(file.get_as_text())
	if err != OK:
		printerr("Godot: Failed to parse JSON: " + json.get_error_message())
		get_tree().quit(1)
		return

	config_data = json.get_data()

	_build_set(config_data.get("set_design", {}))
	_build_lighting(config_data.get("lighting", {}))
	_build_performance(config_data.get("performance", {}))
	_build_camera(config_data.get("camera", {})) # Camera built after to look at actors

	# Wait a bit for physics/rendering to settle before capturing the dailies screenshot
	await get_tree().create_timer(1.0).timeout
	_capture_screenshot("res://dailies.png")

	# Simulating animation time, for example 2 seconds
	await get_tree().create_timer(2.0).timeout

	print("Godot: Render sequence finished.")
	get_tree().quit(0)

func safe_vector3(array_data: Variant, default_val: Vector3) -> Vector3:
	if typeof(array_data) == TYPE_ARRAY and array_data.size() >= 3:
		return Vector3(float(array_data[0]), float(array_data[1]), float(array_data[2]))
	return default_val

func _build_set(set_data: Dictionary) -> void:
	if set_data.is_empty(): return
	var parent_union = CSGCombiner3D.new()
	add_child(parent_union)

	var structures = set_data.get("structures", [])
	for struct_data in structures:
		var type = struct_data.get("type", "csg_box")
		var op = struct_data.get("operation", "union")

		var node: CSGShape3D
		if type == "csg_box":
			node = CSGBox3D.new()
			node.size = safe_vector3(struct_data.get("size"), Vector3(1, 1, 1))
		# Add more types if needed
		else:
			continue

		node.position = safe_vector3(struct_data.get("position"), Vector3.ZERO)

		if op == "subtraction":
			node.operation = CSGShape3D.OPERATION_SUBTRACTION
		else:
			node.operation = CSGShape3D.OPERATION_UNION

		if struct_data.has("color"):
			var material = StandardMaterial3D.new()
			material.albedo_color = Color(struct_data.get("color"))
			node.material = material

		parent_union.add_child(node)

func _build_lighting(light_data: Dictionary) -> void:
	if light_data.is_empty(): return

	# World Environment
	var env = Environment.new()
	var we = WorldEnvironment.new()
	we.environment = env
	add_child(we)

	var ambient = light_data.get("ambient", {})
	if not ambient.is_empty():
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.ambient_light_color = Color(ambient.get("color", "#ffffff"))
		env.ambient_light_energy = ambient.get("energy", 1.0)

	var fog = light_data.get("fog", {})
	if fog.get("enabled", false):
		env.fog_enabled = true
		env.fog_density = fog.get("density", 0.01)

	# Directional Light
	var dir_data = light_data.get("directional", {})
	if not dir_data.is_empty():
		var d_light = DirectionalLight3D.new()
		var direction = dir_data.get("direction", [0, -1, 0])
		d_light.position = Vector3(0, 10, 0)

		# Prevent looking straight down which can cause issues with up vector, or handle it
		var dir_vec = Vector3(direction[0], direction[1], direction[2]).normalized()
		if dir_vec != Vector3.ZERO:
			if abs(dir_vec.y) > 0.999:
				d_light.look_at(d_light.position + dir_vec, Vector3.RIGHT)
			else:
				d_light.look_at(d_light.position + dir_vec)

		d_light.light_energy = dir_data.get("energy", 1.0)
		if dir_data.has("color"):
			d_light.light_color = Color(dir_data.get("color"))
		d_light.shadow_enabled = true
		add_child(d_light)

func _build_camera(cam_data: Dictionary) -> void:
	if cam_data.is_empty(): return
	var camera = Camera3D.new()
	camera.current = true
	add_child(camera)

	camera.position = safe_vector3(cam_data.get("position"), Vector3(0, 2, 5))
	camera.fov = cam_data.get("fov", 75.0)

	var target_vec = safe_vector3(cam_data.get("target"), Vector3(0, 1, 0))
	if camera.position != target_vec:
		camera.look_at(target_vec)

	var movement = cam_data.get("movement", {})
	if not movement.is_empty():
		var type = movement.get("type", "")
		var tween = get_tree().create_tween()
		var speed = movement.get("speed", 2.0)
		if type == "dolly":
			var forward = -camera.global_transform.basis.z
			var dest = camera.position + forward * 2.0
			tween.tween_property(camera, "position", dest, speed)
		elif type == "pan":
			var target_rot = camera.rotation + Vector3(0, deg_to_rad(30), 0)
			tween.tween_property(camera, "rotation", target_rot, speed)
		elif type == "orbit":
			var angle_rad = deg_to_rad(movement.get("angle_deg", 30.0))
			var radius = movement.get("radius", 2.0)

			var cam_offset = camera.position - target_vec
			var current_radius = cam_offset.length()
			# Normalizing offset ignores Y-difference loosely, but simple orbit implementation:
			var dest_pos = target_vec + cam_offset.rotated(Vector3.UP, angle_rad).normalized() * current_radius
			tween.tween_property(camera, "position", dest_pos, speed)

			var dummy_cam = Camera3D.new()
			dummy_cam.position = dest_pos
			dummy_cam.look_at_from_position(dest_pos, target_vec)
			tween.parallel().tween_property(camera, "rotation", dummy_cam.rotation, speed)
			dummy_cam.queue_free()

func _build_performance(perf_data: Dictionary) -> void:
	if perf_data.is_empty(): return
	var sprite = Sprite3D.new()
	sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sprite.name = perf_data.get("actor_id", "actor_01")

	# Fallback placeholder since we might not have a texture generated
	var paths = perf_data.get("path_coords", [])
	if paths.size() > 0:
		sprite.position = safe_vector3(paths[0], Vector3.ZERO)

		if paths.size() > 1:
			var tween = get_tree().create_tween()
			for i in range(1, paths.size()):
				var dest = safe_vector3(paths[i], Vector3.ZERO)
				tween.tween_property(sprite, "position", dest, 1.0)
	else:
		sprite.position = Vector3(0, 0, 0)

	sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	add_child(sprite)

func _capture_screenshot(path: String) -> void:
	var viewport = get_viewport()
	if viewport:
		var image = viewport.get_texture().get_image()
		if image:
			image.save_png(path)
			print("Godot: Saved dailies screenshot to ", path)
