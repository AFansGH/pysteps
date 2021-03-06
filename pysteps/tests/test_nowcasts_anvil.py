# -*- coding: utf-8 -*-

import pytest

from pysteps import motion, nowcasts, verification
from pysteps.tests.helpers import get_precipitation_fields

anvil_arg_names = (
    "n_cascade_levels",
    "ar_order",
    "ar_window_radius",
    "min_csi",
)

anvil_arg_values = [
    (8, 1, 50, 0.6),
    (8, 2, 50, 0.6),
    # (8, 3, 50, 0.6), # This is commented out for the moment since it's a bit unstable (and slow)
]


@pytest.mark.parametrize(anvil_arg_names, anvil_arg_values)
def test_anvil_rainrate(n_cascade_levels, ar_order, ar_window_radius, min_csi):
    """Tests ANVIL nowcast using rain rate precipitation fields."""
    # inputs
    precip_input, metadata = get_precipitation_fields(
        num_prev_files=4,
        num_next_files=0,
        return_raw=False,
        metadata=True,
        upscale=2000,
    )
    precip_input = precip_input.filled()

    precip_obs = get_precipitation_fields(
        num_prev_files=0, num_next_files=3, return_raw=False, upscale=2000
    )[1:, :, :]
    precip_obs = precip_obs.filled()

    # Retrieve motion field
    pytest.importorskip("cv2")
    oflow_method = motion.get_method("LK")
    retrieved_motion = oflow_method(precip_input)

    # Run nowcast
    nowcast_method = nowcasts.get_method("anvil")

    precip_forecast = nowcast_method(
        precip_input[-(ar_order + 2) :],
        retrieved_motion,
        n_timesteps=3,
        rainrate=None,  # no R(VIL) conversion is done
        n_cascade_levels=n_cascade_levels,
        ar_order=ar_order,
        ar_window_radius=ar_window_radius,
    )

    # result
    result = verification.det_cat_fct(
        precip_forecast[-1], precip_obs[-1], thr=0.1, scores="CSI"
    )["CSI"]
    print(f"got CSI={result:.2f}, required > {min_csi:.2f}")
    assert result > min_csi


if __name__ == "__main__":
    for n in range(len(anvil_arg_values)):
        test_args = zip(anvil_arg_names, anvil_arg_values[n])
        test_anvil_rainrate(**dict((x, y) for x, y in test_args))
