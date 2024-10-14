from common.params import Params, ParamKeyType

params = Params()

params.clear_all(ParamKeyType.CLEAR_ON_MANAGER_START)
default_params = [
                ("CompletedTrainingVersion", "1"),
                ("DisengageOnAccelerator", "0"),
                ("HasAcceptedTerms", "1"),
                ("UseAccel", "1"),
                ("F3", "1"),
                ("UseModelPath", "0"),
                ("UseDistSpeed", "0"),
                ("SensitiveSlow", "1"),
                ("WideCameraOnly", "1"),
                ("UbloxAvailable", "1")
                    ]

for k, v in default_params:
    if params.get(k) is None:
        params.put(k, v)
