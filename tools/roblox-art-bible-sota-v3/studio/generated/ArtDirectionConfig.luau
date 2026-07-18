--!strict
-- AUTO-GENERATED. DO NOT EDIT.
-- Source digest: e6e726a74cca7c26fd8121df2daf79f6bf92f81a591bf9b062e4be3622367fb9

local data = {
	artDirection = {
		["$schema"] = "https://roblox-top1.local/schemas/art-direction.schema.json",
		axisContract = {
			blender = {
				upAxis = "Z",
				x = "width",
				y = "depth",
				z = "height",
			},
			conversion = {
				blenderToRoblox = {
					"x",
					"z",
					"y",
				},
				robloxToBlender = {
					"x",
					"z",
					"y",
				},
			},
			designAndRoblox = {
				upAxis = "Y",
				x = "width",
				y = "height",
				z = "depth",
			},
			oneBlenderUnitEqualsStud = true,
			unit = "stud",
		},
		comparisonInvariants = {
			"asset_functions",
			"asset_dimensions",
			"pivots",
			"gameplay_states",
			"triangle_budgets",
			"texture_budgets",
			"camera_rig",
			"lighting_profiles",
			"backgrounds",
			"resolutions",
			"render_passes",
			"revision_rounds",
			"review_questions",
		},
		creativeConstraints = {
			mustCommunicate = {
				"front_back",
				"danger",
				"interaction",
				"damage_state",
				"destruction_direction",
			},
			mustPreserveRobloxAvatarIdentity = true,
			spectacleMustNotOcclude = {
				"direction",
				"target",
				"cause",
				"priority",
			},
			tone = {
				"stylized",
				"expressive",
				"non_gore",
				"lightly_unsettling",
				"occasionally_funny",
				"highly_readable",
			},
		},
		detailHierarchy = {
			deletionRule = "A detail serving neither silhouette, function, nor identity is removed.",
			maskColors = {
				primary = "#FF0000",
				secondary = "#00FF00",
				tertiary = "#0000FF",
			},
			measurementMethod = "detail_band_render_non_overlapping_pixel_masks",
			sumTolerance = 0.02,
			targetProjectedAreaRatio = {
				primary = 0.72,
				secondary = 0.23,
				tertiary = 0.05,
			},
		},
		finalTerritory = "salvaged-frontier",
		forbidden = {
			"thin_loose_wires",
			"floating_fragments_without_gameplay",
			"decorative_microtext",
			"unbounded_grunge",
			"color_only_state",
			"subpixel_silhouette_features",
			"unique_duplicate_mesh_uploads",
			"unlicensed_production_reference",
			"masked_tool_failure",
			"unverified_external_pass",
		},
		gates = {
			automaticSelectionForbidden = true,
			humanSelectionRequired = true,
			requiredHardGateIds = {
				"three_territories_built",
				"human_territory_selection",
				"calibration_kit_coherent",
				"silhouette_recognition_60",
				"function_recognition_mobile",
				"grayscale_and_cvd",
				"materials_four_lights",
				"state_recognition",
				"group_30_visual",
				"roblox_technical_budgets",
				"provenance_complete",
				"weighted_score_90",
				"sixth_asset_transfer_proof",
				"studio_golden_scene",
				"real_device_mobile",
			},
			sixthAssetTransferProofRequired = true,
			weightedScoreMinimum = 90.0,
		},
		productionApproved = false,
		project = {
			genre = "cooperative persistent fortress defense",
			name = "Roblox Top 1",
			northStar = "The fortress is the protagonist; every visual event must preserve cause, direction, target and priority.",
			platformPriority = "mobile-first",
			playerCount = {
				max = 4,
				min = 1,
			},
			visualProtagonist = "player_fortress",
		},
		schemaVersion = "2.0.0",
		screenSpaceRules = {
			bands = {
				primary = {
					distanceStuds = 60.0,
					minimumPixels = 3.0,
					nominalThicknessStuds = 0.610871,
					productionMinimumThicknessStuds = 0.763588,
					productionSafetyFactor = 1.25,
				},
				secondary = {
					distanceStuds = 30.0,
					minimumPixels = 3.0,
					nominalThicknessStuds = 0.305435,
					productionMinimumThicknessStuds = 0.381794,
					productionSafetyFactor = 1.25,
				},
				tertiary = {
					distanceStuds = 15.0,
					minimumPixels = 2.0,
					nominalThicknessStuds = 0.101811,
					productionMinimumThicknessStuds = 0.152717,
					productionSafetyFactor = 1.5,
				},
			},
			calibrationViewport = {
				height = 360,
				width = 640,
			},
			formulaForward = "pixels = viewportHeight * (2*atan(thickness/(2*distance))) / verticalFovRadians",
			formulaInverse = "thickness = 2*distance*tan((pixels/viewportHeight*verticalFovRadians)/2)",
			projectionModel = "exact_angular_vertical_fov",
			recalibrationRule = "Any FOV, FieldOfViewMode, camera distance, or validation resolution change invalidates prior thresholds.",
			verticalFieldOfViewDegrees = 70.0,
		},
		status = "CANDIDATE_SELECTED",
		territories = {
			"industrial-toy-defense",
			"salvaged-frontier",
			"clean-tactical-diorama",
		},
		version = "0.3.0",
	},
	calibrationKit = {
		["$schema"] = "https://roblox-top1.local/schemas/calibration-kit.schema.json",
		assets = {
			barricade = {
				dimensions = {
					depth = 2.0,
					height = 4.0,
					width = 8.0,
				},
				["function"] = "temporary path-blocking defensive structure",
				pivot = "bottom_center",
				requiredStateVariants = {
					"intact",
					"damaged",
					"critical",
				},
				targetReadDistanceStuds = 60,
				textureBudgetClass = "medium",
				triangleBudgetMax = 2000,
			},
			damage_effect = {
				dimensions = {
					depth = 4.0,
					height = 4.0,
					width = 4.0,
				},
				["function"] = "communicate hit direction, damage severity and impact cause",
				pivot = "impact_center",
				requiredStateVariants = {
					"damaged",
					"critical",
				},
				targetReadDistanceStuds = 30,
				textureBudgetClass = "small",
				timingSeconds = {
					hitFlashMax = 0.12,
					primaryShape = 0.35,
					residualMax = 1.2,
				},
				triangleBudgetMax = 300,
			},
			enemy_standard = {
				dimensions = {
					depth = 2.5,
					height = 5.5,
					width = 2.5,
				},
				["function"] = "standard walking horde enemy",
				pivot = "feet_center",
				requiredStateVariants = {
					"intact",
					"damaged",
					"critical",
				},
				targetReadDistanceStuds = 60,
				textureBudgetClass = "medium",
				triangleBudgetMax = 5000,
			},
			floor_module = {
				dimensions = {
					depth = 4.0,
					height = 0.5,
					width = 4.0,
				},
				["function"] = "repeatable fortress floor cell",
				pivot = "bottom_center",
				requiredStateVariants = {
					"intact",
					"damaged",
				},
				targetReadDistanceStuds = 30,
				textureBudgetClass = "small",
				triangleBudgetMax = 800,
			},
			objective_core = {
				dimensions = {
					depth = 6.0,
					height = 7.0,
					width = 6.0,
				},
				["function"] = "primary defendable objective and visual anchor",
				pivot = "bottom_center",
				requiredStateVariants = {
					"intact",
					"damaged",
					"critical",
				},
				targetReadDistanceStuds = 60,
				textureBudgetClass = "medium",
				triangleBudgetMax = 4500,
			},
		},
		axisContractRef = "art/art-direction.json#/axisContract",
		goldenScene = {
			avatar = {
				heightReference = true,
				rig = "R15",
			},
			grounds = {
				"world_neutral_light",
				"world_neutral_dark",
			},
			isolatedCopiesPerVariant = 1,
			requiredProfiles = {
				"Lighting_Gameplay_Default",
				"Lighting_HighContrast",
				"Lighting_Adverse_Night",
				"Lighting_Neutral_QA",
			},
			size = {
				depth = 600.0,
				width = 160.0,
			},
			stressCopyCounts = {
				30,
				100,
			},
			zones = {
				"avatar_grid",
				"isolated_light",
				"isolated_dark",
				"states",
				"stress_30",
				"stress_100",
				"mixed_gameplay",
				"graybox_reference",
			},
		},
		schemaVersion = "3.0.0",
		sharedRules = {
			dimensionToleranceStuds = 0.005,
			dimensionsMustMatchAcrossTerritories = true,
			materialSlotsMaxPerMesh = 1,
			noFinalTexturesBeforeTerritorySelection = true,
			pivotToleranceStuds = 0.002,
			pivotsMustMatchAcrossTerritories = true,
			revisionRoundsPerTerritory = 2,
			states = {
				"intact",
				"damaged",
				"critical",
			},
			triangleBudgetTolerance = 0,
			uvSetsMaxPerMesh = 1,
		},
		status = "LOCKED_FOR_COMPARISON",
		textureClasses = {
			large = {
				albedoMax = 1024,
				maxAssetExtentStuds = 20.0,
				nonAlbedoMax = 1024,
			},
			medium = {
				albedoMax = 512,
				maxAssetExtentStuds = 10.0,
				nonAlbedoMax = 512,
			},
			small = {
				albedoMax = 256,
				maxAssetExtentStuds = 5.0,
				nonAlbedoMax = 256,
			},
			tiny = {
				albedoMax = 128,
				maxAssetExtentStuds = 2.0,
				nonAlbedoMax = 128,
			},
		},
		unit = "stud",
	},
	cameraRig = {
		["$schema"] = "https://roblox-top1.local/schemas/camera-rig.schema.json",
		backgrounds = {
			"world_neutral_light",
			"world_neutral_dark",
		},
		cameraValidation = {
			positionToleranceStuds = 0.005,
			rotationToleranceDegrees = 0.01,
			verticalFovToleranceDegrees = 0.01,
		},
		coordinateContract = {
			forwardAxis = "-Z in Blender camera local space",
			lookAt = "fixed target point",
			positionFormula = "target + spherical(distance, azimuth, elevation)",
			targetPoint = "fixed world point per camera, expressed in Blender X/Y/Z after axis conversion",
		},
		fieldOfView = {
			degrees = 70.0,
			mode = "Vertical",
		},
		gameplayCamera = {
			azimuthDegrees = 25.0,
			distanceStuds = 16.0,
			elevationDegrees = 18.0,
			targetHeightStuds = 2.5,
		},
		resolutions = {
			{
				height = 360,
				id = "mobile_landscape_hard",
				orientation = "landscape",
				required = true,
				width = 640,
			},
			{
				height = 540,
				id = "mobile_landscape_mid",
				orientation = "landscape",
				required = true,
				width = 960,
			},
			{
				height = 720,
				id = "reference_landscape",
				orientation = "landscape",
				required = true,
				width = 1280,
			},
			{
				height = 640,
				id = "mobile_narrow_portrait",
				orientation = "portrait",
				required = true,
				width = 360,
			},
			{
				height = 960,
				id = "mobile_tall_portrait",
				orientation = "portrait",
				required = false,
				width = 540,
			},
		},
		rule = "Any camera contract change requires a schema-versioned recalibration and invalidates prior screen-space evidence.",
		schemaVersion = "2.0.0",
		validationCameras = {
			back = {
				azimuthDegrees = 180.0,
				derivedCameraHeightStuds = 4.145129,
				distanceStuds = 20.0,
				elevationDegrees = 4.0,
				targetHeightStuds = 2.75,
			},
			far = {
				azimuthDegrees = 35.0,
				derivedCameraHeightStuds = 13.684132,
				distanceStuds = 60.0,
				elevationDegrees = 10.5,
				targetHeightStuds = 2.75,
			},
			front = {
				azimuthDegrees = 0.0,
				derivedCameraHeightStuds = 4.145129,
				distanceStuds = 20.0,
				elevationDegrees = 4.0,
				targetHeightStuds = 2.75,
			},
			mid = {
				azimuthDegrees = 35.0,
				derivedCameraHeightStuds = 8.987351,
				distanceStuds = 30.0,
				elevationDegrees = 12.0,
				targetHeightStuds = 2.75,
			},
			near = {
				azimuthDegrees = 35.0,
				derivedCameraHeightStuds = 6.378828,
				distanceStuds = 15.0,
				elevationDegrees = 14.0,
				targetHeightStuds = 2.75,
			},
			three_quarter = {
				azimuthDegrees = 35.0,
				derivedCameraHeightStuds = 8.814022,
				distanceStuds = 22.0,
				elevationDegrees = 16.0,
				targetHeightStuds = 2.75,
			},
		},
	},
	renderMatrix = {
		["$schema"] = "https://roblox-top1.local/schemas/render-matrix.schema.json",
		comparisonRule = "A mode expands the calibration kit's applicable asset/state pairs identically for all territories; per-territory omissions are invalid.",
		coveragePolicy = {
			fullModeRequiredCoverage = {
				allApplicableStatesInBeauty = true,
				allApplicableStatesInSilhouette = true,
				allAssets = true,
				allCanonicalDistancesInBeauty = true,
				allDiagnosticPasses = true,
				allLightingProfilesInBeauty = true,
				allRequiredResolutions = true,
				bothBackgroundsInBeauty = true,
				frontBackThreeQuarterSilhouette = true,
			},
			method = "risk_based_constrained_combinatorial_matrix",
			perTerritoryOmissionsForbidden = true,
			rationale = "Avoid a brute-force Cartesian explosion while guaranteeing every gameplay state, canonical distance, lighting profile, background, required resolution, silhouette orientation and diagnostic pass is exercised in an explicit job.",
		},
		fileNameTemplate = "{territory}__{asset}__{state}__{camera}__{lighting}__{background}__{resolution}__{pass}.png",
		groupScenes = {
			{
				assetId = "barricade",
				count = 30,
				id = "stress_barricade_30",
			},
			{
				assetId = "enemy_standard",
				count = 30,
				id = "stress_enemy_30",
			},
			{
				assetId = "objective_core",
				count = 1,
				id = "mixed_gameplay",
			},
		},
		modes = {
			full = {
				evidenceTier = "BLENDER_PREFLIGHT_COMPLETE",
				expectedRenderCount = 421,
				jobs = {
					{
						assetIds = {
							"barricade",
							"objective_core",
							"enemy_standard",
							"floor_module",
							"damage_effect",
						},
						backgroundIds = {
							"world_neutral_light",
							"world_neutral_dark",
						},
						cameraIds = {
							"near",
							"mid",
							"far",
						},
						jobId = "semantic_state_lighting",
						lightingProfileIds = {
							"Lighting_Gameplay_Default",
							"Lighting_HighContrast",
							"Lighting_Adverse_Night",
							"Lighting_Neutral_QA",
						},
						passIds = {
							"beauty",
						},
						resolutionIds = {
							"mobile_landscape_hard",
						},
						stateIds = {
							"intact",
							"damaged",
							"critical",
						},
					},
					{
						assetIds = {
							"barricade",
							"objective_core",
							"enemy_standard",
							"floor_module",
							"damage_effect",
						},
						backgroundIds = {
							"world_neutral_light",
							"world_neutral_dark",
						},
						cameraIds = {
							"far",
							"front",
							"back",
							"three_quarter",
						},
						jobId = "orientation_silhouette",
						lightingProfileIds = {
							"Lighting_Gameplay_Default",
							"Lighting_Adverse_Night",
						},
						passIds = {
							"silhouette",
						},
						resolutionIds = {
							"mobile_landscape_hard",
						},
						stateIds = {
							"intact",
						},
					},
					{
						assetIds = {
							"barricade",
							"objective_core",
							"enemy_standard",
							"floor_module",
							"damage_effect",
						},
						backgroundIds = {
							"world_neutral_light",
						},
						cameraIds = {
							"near",
						},
						jobId = "state_silhouette_comparison",
						lightingProfileIds = {
							"Lighting_Neutral_QA",
						},
						passIds = {
							"silhouette",
						},
						resolutionIds = {
							"mobile_landscape_hard",
						},
						stateIds = {
							"intact",
							"damaged",
							"critical",
						},
					},
					{
						assetIds = {
							"barricade",
							"objective_core",
							"enemy_standard",
							"floor_module",
							"damage_effect",
						},
						backgroundIds = {
							"world_neutral_light",
							"world_neutral_dark",
						},
						cameraIds = {
							"near",
						},
						jobId = "material_and_detail_qa",
						lightingProfileIds = {
							"Lighting_Neutral_QA",
						},
						passIds = {
							"flat_albedo",
							"detail_band",
						},
						resolutionIds = {
							"mobile_landscape_hard",
						},
						stateIds = {
							"intact",
						},
					},
					{
						assetIds = {
							"barricade",
							"objective_core",
							"enemy_standard",
							"floor_module",
							"damage_effect",
						},
						backgroundIds = {
							"world_neutral_dark",
						},
						cameraIds = {
							"three_quarter",
						},
						jobId = "resolution_orientation_framing",
						lightingProfileIds = {
							"Lighting_Gameplay_Default",
						},
						passIds = {
							"beauty",
						},
						resolutionIds = {
							"mobile_landscape_hard",
							"mobile_landscape_mid",
							"reference_landscape",
							"mobile_narrow_portrait",
						},
						stateIds = {
							"critical",
						},
					},
				},
			},
			smoke = {
				evidenceTier = "PREVIEW_ONLY",
				expectedRenderCount = 108,
				jobs = {
					{
						assetIds = {
							"barricade",
							"objective_core",
							"enemy_standard",
							"floor_module",
							"damage_effect",
						},
						backgroundIds = {
							"world_neutral_light",
							"world_neutral_dark",
						},
						cameraIds = {
							"near",
							"mid",
							"far",
						},
						jobId = "mobile_semantic_smoke",
						lightingProfileIds = {
							"Lighting_Gameplay_Default",
							"Lighting_Adverse_Night",
						},
						passIds = {
							"beauty",
						},
						resolutionIds = {
							"mobile_landscape_hard",
						},
						stateIds = {
							"intact",
							"critical",
						},
					},
					{
						assetIds = {
							"barricade",
							"objective_core",
							"enemy_standard",
							"floor_module",
							"damage_effect",
						},
						backgroundIds = {
							"world_neutral_light",
							"world_neutral_dark",
						},
						cameraIds = {
							"far",
						},
						jobId = "far_silhouette_smoke",
						lightingProfileIds = {
							"Lighting_Neutral_QA",
						},
						passIds = {
							"silhouette",
						},
						resolutionIds = {
							"mobile_landscape_hard",
						},
						stateIds = {
							"intact",
						},
					},
					{
						assetIds = {
							"barricade",
							"objective_core",
							"enemy_standard",
							"floor_module",
							"damage_effect",
						},
						backgroundIds = {
							"world_neutral_light",
						},
						cameraIds = {
							"near",
						},
						jobId = "detail_band_smoke",
						lightingProfileIds = {
							"Lighting_Neutral_QA",
						},
						passIds = {
							"detail_band",
						},
						resolutionIds = {
							"mobile_landscape_hard",
						},
						stateIds = {
							"intact",
						},
					},
				},
			},
		},
		schemaVersion = "3.0.0",
	},
	semanticPalette = {
		["$schema"] = "https://roblox-top1.local/schemas/semantic-palette.schema.json",
		accessibility = {
			colorNeverSoleCarrier = true,
			cvdModel = "Machado_2009_100_percent_matrices",
			minimumBoundaryContrastProxy = 3.0,
			neutralQaBehaviorRequired = true,
			requiredTransforms = {
				"grayscale",
				"protanopia",
				"deuteranopia",
				"tritanopia",
			},
			textContrastWhenUsed = 4.5,
			threeLightingBehaviorRequired = {
				"Gameplay_Default",
				"HighContrast",
				"Adverse_Night",
			},
		},
		colorSpace = "sRGB",
		roles = {
			critical = {
				hex = "#E64A4A",
				maxVisibleAreaRatio = 0.08,
				minimumLocalContrastRatio = 3.0,
				redundantCue = {
					audio = "critical_alarm",
					motion = "double_pulse",
					shape = "broken_double_chevron",
				},
			},
			disabled = {
				hex = "#68717F",
				maxVisibleAreaRatio = 0.2,
				minimumLocalContrastRatio = 2.0,
				redundantCue = {
					audio = "disabled_click",
					motion = "none",
					shape = "open_ring_or_crossbar",
				},
			},
			enemy_threat = {
				hex = "#A84876",
				maxVisibleAreaRatio = 0.16,
				minimumLocalContrastRatio = 3.0,
				redundantCue = {
					audio = "threat_vocal",
					motion = "hostile_stride",
					shape = "hostile_forward_mass_or_face",
				},
			},
			interactive_ready = {
				hex = "#61E7C4",
				maxVisibleAreaRatio = 0.1,
				minimumLocalContrastRatio = 3.0,
				redundantCue = {
					audio = "ready_chime",
					motion = "slow_single_pulse",
					shape = "complete_ring",
				},
			},
			objective_anchor = {
				hex = "#66A3FF",
				maxVisibleAreaRatio = 0.14,
				minimumLocalContrastRatio = 3.0,
				redundantCue = {
					audio = "core_hum",
					motion = "stable_breath",
					shape = "concentric_core",
				},
			},
			player_buildable = {
				hex = "#D58B31",
				maxVisibleAreaRatio = 0.18,
				minimumLocalContrastRatio = 3.0,
				redundantCue = {
					audio = "build_confirm",
					motion = "placement_ghost",
					shape = "thick_frame_or_socket",
				},
			},
			warning = {
				hex = "#F2C94C",
				maxVisibleAreaRatio = 0.08,
				minimumLocalContrastRatio = 3.0,
				redundantCue = {
					audio = "warning_tick",
					motion = "medium_pulse",
					shape = "single_chevron",
				},
			},
			world_neutral_dark = {
				hex = "#354052",
				maxVisibleAreaRatio = 0.55,
				minimumLocalContrastRatio = 1.0,
				redundantCue = {
					audio = "none",
					motion = "none",
					shape = "large_supporting_mass",
				},
			},
			world_neutral_light = {
				hex = "#D8DDE4",
				maxVisibleAreaRatio = 0.45,
				minimumLocalContrastRatio = 1.0,
				redundantCue = {
					audio = "none",
					motion = "none",
					shape = "large_supporting_plane",
				},
			},
		},
		schemaVersion = "2.0.0",
		stateEncoding = {
			critical = {
				audioCue = "alarm",
				motionCue = "double_pulse",
				primaryRole = "critical",
				shapeCue = "two_or_more_major_breaks_and_exposed_core",
			},
			damaged = {
				audioCue = "strained",
				motionCue = "irregular_single_pulse",
				primaryRole = "warning",
				shapeCue = "one_major_break_or_offset",
			},
			disabled = {
				audioCue = "low_click",
				motionCue = "none",
				primaryRole = "disabled",
				shapeCue = "open_circuit_or_crossbar",
			},
			intact = {
				audioCue = "clean",
				motionCue = "stable",
				primaryRole = "interactive_ready",
				shapeCue = "continuous_outline",
			},
		},
	},
	visualRubric = {
		["$schema"] = "https://roblox-top1.local/schemas/visual-rubric.schema.json",
		dimensions = {
			functionalReadability = {
				floor = 4.0,
				question = "Can players identify function and interaction under pressure?",
				weight = 20.0,
			},
			identityDistinctiveness = {
				floor = 3.0,
				question = "Is the territory memorable and commercially distinct without copying a reference?",
				weight = 15.0,
			},
			materialLightingRobustness = {
				floor = 3.0,
				question = "Do materials retain identity and hierarchy under all four lights?",
				weight = 10.0,
			},
			mobileClutterControl = {
				floor = 4.0,
				question = "Does the scene remain legible at hard mobile resolution and in a group of 30?",
				weight = 10.0,
			},
			modularityReuse = {
				floor = 3.0,
				question = "Can meshes, materials and modules be reused while preserving variety?",
				weight = 5.0,
			},
			productionScalability = {
				floor = 3.0,
				question = "Can a small team produce many assets without escalating complexity?",
				weight = 5.0,
			},
			roleStateDifferentiation = {
				floor = 4.0,
				question = "Are factions, roles and states distinct without color-only dependence?",
				weight = 15.0,
			},
			silhouetteHierarchy = {
				floor = 4.0,
				question = "Do primary, secondary and tertiary forms read at intended distances?",
				weight = 15.0,
			},
			technicalFitness = {
				floor = 4.0,
				question = "Does the territory meet deterministic and calibrated technical gates?",
				weight = 5.0,
			},
		},
		hardGates = {
			deterministic_rules = {
				kind = "technical_boolean",
			},
			function_recognition_mobile = {
				kind = "task_rate",
				minimumCorrectRate = 0.875,
				minimumParticipants = 8,
				taskGroupId = "function_30_mobile",
			},
			grayscale_and_cvd = {
				kind = "technical_boolean",
			},
			group_30_visual = {
				kind = "technical_boolean",
			},
			materials_four_lights = {
				kind = "technical_boolean",
			},
			not_color_only = {
				kind = "technical_boolean",
			},
			provenance_complete = {
				kind = "technical_boolean",
			},
			real_device_mobile = {
				kind = "technical_boolean",
			},
			roblox_technical_budgets = {
				kind = "technical_boolean",
			},
			silhouette_recognition_60 = {
				kind = "task_rate",
				minimumCorrectRate = 0.75,
				minimumParticipants = 8,
				taskGroupId = "silhouette_60",
			},
			state_recognition = {
				kind = "task_rate",
				minimumCorrectRate = 0.875,
				minimumParticipants = 8,
				taskGroupId = "state_15_30",
			},
			studio_golden_scene = {
				kind = "technical_boolean",
			},
		},
		reviewPolicy = {
			automaticSelectionForbidden = true,
			blindMapStoredSeparately = true,
			blindTerritoryLabels = true,
			humanSelectionRequired = true,
			maximumPostReconciliationDisagreement = 1.0,
			minimumExpertReviewers = 2,
			minimumMedianConfidence = 0.7,
			minimumTaskParticipants = 8,
			smallSampleInterpretation = "directional_gate_not_population_estimate",
		},
		scale = {
			max = 5,
			min = 1,
		},
		schemaVersion = "2.0.0",
		weightedScoreMinimum = 90.0,
	},
}
data.sourceDigest = "e6e726a74cca7c26fd8121df2daf79f6bf92f81a591bf9b062e4be3622367fb9"

return table.freeze(data)
