--!strict
-- AUTO-GENERATED. DO NOT EDIT.
-- Source digest: 39bc4fc759bda57824c3ae303830e5b330fdde3f67bfdd20ac9e4b9bf9d8dcba

local data = {
	["$schema"] = "https://roblox-top1.local/schemas/lighting-profiles.schema.json",
	profiles = {
		Lighting_Adverse_Night = {
			readbackTolerance = {
				booleanExact = true,
				colorChannel = 0,
				numberAbsolute = 0.0001,
			},
			scriptMutable = {
				Atmosphere = {
					Color = {
						86,
						111,
						151,
					},
					Decay = {
						18,
						28,
						48,
					},
					Density = 0.28,
					Glare = 0.0,
					Haze = 1.2,
					Offset = 0.12,
				},
				BloomEffect = {
					Enabled = true,
					Intensity = 0.2,
					Size = 18.0,
					Threshold = 1.1,
				},
				ColorCorrectionEffect = {
					Brightness = 0.04,
					Contrast = 0.08,
					Saturation = -0.08,
					TintColor = {
						214,
						226,
						255,
					},
				},
				Lighting = {
					Ambient = {
						36,
						44,
						68,
					},
					Brightness = 1.8,
					ClockTime = 0.5,
					ColorShift_Bottom = {
						8,
						12,
						22,
					},
					ColorShift_Top = {
						74,
						104,
						158,
					},
					EnvironmentDiffuseScale = 0.5,
					EnvironmentSpecularScale = 0.55,
					ExposureCompensation = 0.35,
					GeographicLatitude = 20.0,
					GlobalShadows = true,
					OutdoorAmbient = {
						68,
						84,
						112,
					},
					ShadowSoftness = 0.4,
				},
			},
			studioManualPreconditions = {
				LightingStyle = "Realistic",
				PrioritizeLightingQuality = false,
			},
		},
		Lighting_Gameplay_Default = {
			readbackTolerance = {
				booleanExact = true,
				colorChannel = 0,
				numberAbsolute = 0.0001,
			},
			scriptMutable = {
				Atmosphere = {
					Color = {
						199,
						213,
						225,
					},
					Decay = {
						92,
						105,
						125,
					},
					Density = 0.18,
					Glare = 0.0,
					Haze = 0.7,
					Offset = 0.08,
				},
				BloomEffect = {
					Enabled = false,
					Intensity = 0.0,
					Size = 24.0,
					Threshold = 1.0,
				},
				ColorCorrectionEffect = {
					Brightness = 0.0,
					Contrast = 0.08,
					Saturation = -0.05,
					TintColor = {
						255,
						252,
						246,
					},
				},
				Lighting = {
					Ambient = {
						55,
						60,
						70,
					},
					Brightness = 2.2,
					ClockTime = 14.0,
					ColorShift_Bottom = {
						18,
						24,
						34,
					},
					ColorShift_Top = {
						255,
						245,
						226,
					},
					EnvironmentDiffuseScale = 0.65,
					EnvironmentSpecularScale = 0.45,
					ExposureCompensation = 0.0,
					GeographicLatitude = 25.0,
					GlobalShadows = true,
					OutdoorAmbient = {
						126,
						132,
						145,
					},
					ShadowSoftness = 0.65,
				},
			},
			studioManualPreconditions = {
				LightingStyle = "Realistic",
				PrioritizeLightingQuality = false,
			},
		},
		Lighting_HighContrast = {
			readbackTolerance = {
				booleanExact = true,
				colorChannel = 0,
				numberAbsolute = 0.0001,
			},
			scriptMutable = {
				Atmosphere = {
					Color = {
						216,
						224,
						232,
					},
					Decay = {
						104,
						112,
						126,
					},
					Density = 0.08,
					Glare = 0.0,
					Haze = 0.2,
					Offset = 0.0,
				},
				BloomEffect = {
					Enabled = false,
					Intensity = 0.0,
					Size = 24.0,
					Threshold = 1.0,
				},
				ColorCorrectionEffect = {
					Brightness = 0.0,
					Contrast = 0.22,
					Saturation = -0.08,
					TintColor = {
						255,
						247,
						236,
					},
				},
				Lighting = {
					Ambient = {
						32,
						36,
						44,
					},
					Brightness = 2.8,
					ClockTime = 11.0,
					ColorShift_Bottom = {
						8,
						12,
						20,
					},
					ColorShift_Top = {
						255,
						232,
						196,
					},
					EnvironmentDiffuseScale = 0.6,
					EnvironmentSpecularScale = 0.55,
					ExposureCompensation = -0.15,
					GeographicLatitude = 35.0,
					GlobalShadows = true,
					OutdoorAmbient = {
						112,
						118,
						128,
					},
					ShadowSoftness = 0.2,
				},
			},
			studioManualPreconditions = {
				LightingStyle = "Realistic",
				PrioritizeLightingQuality = true,
			},
		},
		Lighting_Neutral_QA = {
			readbackTolerance = {
				booleanExact = true,
				colorChannel = 0,
				numberAbsolute = 0.0001,
			},
			scriptMutable = {
				Atmosphere = {
					Color = {
						255,
						255,
						255,
					},
					Decay = {
						255,
						255,
						255,
					},
					Density = 0.0,
					Glare = 0.0,
					Haze = 0.0,
					Offset = 0.0,
				},
				BloomEffect = {
					Enabled = false,
					Intensity = 0.0,
					Size = 24.0,
					Threshold = 1.0,
				},
				ColorCorrectionEffect = {
					Brightness = 0.0,
					Contrast = 0.0,
					Saturation = 0.0,
					TintColor = {
						255,
						255,
						255,
					},
				},
				Lighting = {
					Ambient = {
						128,
						128,
						128,
					},
					Brightness = 2.0,
					ClockTime = 12.0,
					ColorShift_Bottom = {
						255,
						255,
						255,
					},
					ColorShift_Top = {
						255,
						255,
						255,
					},
					EnvironmentDiffuseScale = 0.5,
					EnvironmentSpecularScale = 0.25,
					ExposureCompensation = 0.0,
					GeographicLatitude = 0.0,
					GlobalShadows = false,
					OutdoorAmbient = {
						128,
						128,
						128,
					},
					ShadowSoftness = 1.0,
				},
			},
			studioManualPreconditions = {
				LightingStyle = "Soft",
				PrioritizeLightingQuality = false,
			},
		},
	},
	protectedPropertyPolicy = {
		behavior = "manual_studio_precondition_then_readback",
		failureMode = "FAIL_PROFILE_APPLICATION",
		properties = {
			"LightingStyle",
			"PrioritizeLightingQuality",
		},
	},
	schemaVersion = "2.0.0",
	status = "CALIBRATION",
}
data.sourceDigest = "39bc4fc759bda57824c3ae303830e5b330fdde3f67bfdd20ac9e4b9bf9d8dcba"

return table.freeze(data)
