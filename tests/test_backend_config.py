from case5_unit_commitment import BackendConfig, NoiseConfig


def test_local_backend_defaults_are_offline():
    assert BackendConfig.from_environment("statevector").shots == -1
    sampled = BackendConfig.from_environment("local_fake", shots=64)
    assert sampled.mode == "local_fake"
    assert sampled.shots == 64
    noisy = BackendConfig.from_environment("local_noisy", shots=32, noise_profile="moderate")
    assert noisy.noise is not None
    assert noisy.noise.name == "moderate"


def test_noise_profile_rejects_invalid_probability():
    try:
        NoiseConfig(readout_bit_flip=1.1)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid readout probability was accepted")
