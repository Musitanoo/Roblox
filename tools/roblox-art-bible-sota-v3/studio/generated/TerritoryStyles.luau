--!strict
-- AUTO-GENERATED. DO NOT EDIT.
-- Source digest: 373fa09c83ea353f4fc10183d21d085c5aa0d1a668348ecf0943edaee081aa45

local data = {
	roleProfiles = {
		accent = {
			blender = {
				coat = 0.22,
				emission = 0.0,
				metallic = 0.12,
				roughness = 0.44,
			},
			studio = {
				castShadow = true,
				material = "SmoothPlastic",
			},
		},
		bareMetal = {
			blender = {
				coat = 0.08,
				emission = 0.0,
				metallic = 0.92,
				roughness = 0.3,
			},
			studio = {
				castShadow = true,
				material = "Metal",
			},
		},
		critical = {
			blender = {
				coat = 0.1,
				emission = 0.0,
				metallic = 0.02,
				roughness = 0.48,
			},
			studio = {
				castShadow = true,
				material = "SmoothPlastic",
			},
		},
		interaction = {
			blender = {
				coat = 0.34,
				emission = 0.65,
				metallic = 0.0,
				roughness = 0.24,
			},
			studio = {
				castShadow = false,
				material = "Neon",
			},
		},
		primary = {
			blender = {
				coat = 0.18,
				emission = 0.0,
				metallic = 0.05,
				roughness = 0.52,
			},
			studio = {
				castShadow = true,
				material = "SmoothPlastic",
			},
		},
		rubber = {
			blender = {
				coat = 0.0,
				emission = 0.0,
				metallic = 0.0,
				roughness = 0.92,
			},
			studio = {
				castShadow = true,
				material = "Rubber",
			},
		},
		secondary = {
			blender = {
				coat = 0.08,
				emission = 0.0,
				metallic = 0.0,
				roughness = 0.68,
			},
			studio = {
				castShadow = true,
				material = "SmoothPlastic",
			},
		},
		threat = {
			blender = {
				coat = 0.12,
				emission = 0.0,
				metallic = 0.02,
				roughness = 0.56,
			},
			studio = {
				castShadow = true,
				material = "SmoothPlastic",
			},
		},
		warning = {
			blender = {
				coat = 0.12,
				emission = 0.0,
				metallic = 0.03,
				roughness = 0.44,
			},
			studio = {
				castShadow = true,
				material = "SmoothPlastic",
			},
		},
	},
	schemaVersion = "1.0.0",
	surfaceProfiles = {
		bare_metal = {
			studioMaterial = "Metal",
		},
		concrete = {
			studioMaterial = "Concrete",
		},
		painted_metal = {
			studioMaterial = "SmoothPlastic",
		},
		polymer = {
			studioMaterial = "SmoothPlastic",
		},
		reclaimed_composite = {
			studioMaterial = "SmoothPlastic",
		},
		reclaimed_wood = {
			studioMaterial = "WoodPlanks",
		},
		rubber = {
			studioMaterial = "Rubber",
		},
	},
	territories = {
		["clean-tactical-diorama"] = {
			palette = {
				accent = "#4C83C3",
				bareMetal = "#94A1AE",
				critical = "#E64A4A",
				interaction = "#61E7C4",
				primary = "#3D485A",
				rubber = "#202733",
				secondary = "#E3E8ED",
				threat = "#9B4660",
				warning = "#F2C94C",
			},
			surfaceAssignments = {
				accent = "painted_metal",
				bareMetal = "bare_metal",
				critical = "polymer",
				interaction = "polymer",
				primary = "polymer",
				rubber = "rubber",
				secondary = "concrete",
				threat = "polymer",
				warning = "polymer",
			},
		},
		["industrial-toy-defense"] = {
			palette = {
				accent = "#E05A16",
				bareMetal = "#687380",
				critical = "#E64A4A",
				interaction = "#17D8EA",
				primary = "#354052",
				rubber = "#171B22",
				secondary = "#AEB8C6",
				threat = "#A84865",
				warning = "#F2C94C",
			},
			surfaceAssignments = {
				accent = "painted_metal",
				bareMetal = "bare_metal",
				critical = "polymer",
				interaction = "polymer",
				primary = "painted_metal",
				rubber = "rubber",
				secondary = "polymer",
				threat = "painted_metal",
				warning = "polymer",
			},
		},
		["salvaged-frontier"] = {
			palette = {
				accent = "#C7763E",
				bareMetal = "#7F8783",
				critical = "#E4524E",
				interaction = "#5FE0C1",
				primary = "#343A3C",
				rubber = "#202322",
				secondary = "#B8AD96",
				threat = "#9D455B",
				warning = "#E5B94A",
			},
			surfaceAssignments = {
				accent = "painted_metal",
				bareMetal = "bare_metal",
				critical = "polymer",
				interaction = "polymer",
				primary = "painted_metal",
				rubber = "rubber",
				secondary = "reclaimed_composite",
				threat = "reclaimed_composite",
				warning = "polymer",
			},
		},
	},
}
data.sourceDigest = "373fa09c83ea353f4fc10183d21d085c5aa0d1a668348ecf0943edaee081aa45"

return table.freeze(data)
