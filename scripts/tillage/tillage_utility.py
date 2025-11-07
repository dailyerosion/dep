def operation_maker(crop, tillage_class, last_crop="C"):
    if crop in ["U", "F"]:
        return ""
    tillage_number = tillage_class - 1

    Croptype_dict = {
        "C": "rowcrop",
        "B": "rowcrop",
        "G": "grass",
        "P": "grass",
    }
    croptype = Croptype_dict[crop]

    Spring_op_list = [
        ["notill", "notill"],
        ["fieldcultivate", "fieldcultivate"],
        ["fieldcultivate", "fieldcultivate_disc"],
        ["fieldcultivate_discx2", "fieldcultivate"],
        ["fieldcultivate_disc", "fieldcultivate_disc"],
    ]

    Fall_operations = {
        "B": ["notill", "notill", "chisel", "chisel", "moldboard"],
        "C": ["notill", "chisel", "chisel", "moldboard", "moldboard"],
    }

    if last_crop == "C":
        spring = Spring_op_list[tillage_number][1]
    else:
        spring = Spring_op_list[tillage_number][0]

    if tillage_class == 1:
        intensity = "notill"
    else:
        intensity = "conventional"

    fall = Fall_operations.get(crop, [""] * 6)[tillage_number]

    with open(
        "operations/spring_tillage/spring_%s_%s.txt" % (croptype, spring), "r"
    ) as f:
        spring_tillage = f.readlines()
    with open(
        "operations/planting/planting_%s_%s.txt" % (croptype, intensity), "r"
    ) as f:
        planting = f.readlines()
    with open("operations/harvest/harvest_%s.txt" % (croptype), "r") as f:
        harvest = f.readlines()
    with open(
        "operations/fall_tillage/fall_%s_%s.txt" % (croptype, fall), "r"
    ) as f:
        fall_tillage = f.readlines()
    everything = spring_tillage + planting + harvest + fall_tillage
    return "".join(everything)
