"""Displacment estimators"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calc_kasai(I, Q, taxis: int = 2, fd = None, c: float = 1540.0, ksize: int = 1, kaxis: int = 0, mode='cumsum'):
    """Calculte small scale displacement via Kasai algorithm

    Parameters:
    ----
    `I`: in phase component of signal
    `Q`: quadrature component of the signal
    `taxis`: axis of tensor over which to calculate phase shift (big-time)
    `c`: speed of sound in m/s
    `ksize`: size of the averaging kernel in pixels
    `kaxis`: axis over wich to apply kernel (fast time)
    `fd`: demodulation frequency in Hz
    `mode`: 'cumsum' or 'differential'

    Returns:
    ----
    `disp`: displacement information
    """

    # Scales by wavelength if system information is provided
    if fd is None:
        _scale = 1
        logger.info('Displacements returned in radians.')
    else:
        _scale = (c / 2) * 1e6 / (2 * np.pi * fd)
        logger.info('Scaling returned displacements to microns.')

    # Isolate t(0) to t(N-1)
    _t0_slicer = [slice(I.shape[ind]) for ind in range(len(I.shape))]
    _t0_slicer[taxis] = slice(I.shape[taxis]-1)
    _t0_slicer = tuple(_t0_slicer)
    _i_0 = I[_t0_slicer]
    _q_0 = Q[_t0_slicer]

    # Isolate t(1) to t(N)
    _t1_slicer = [slice(I.shape[ind]) for ind in range(len(I.shape))]
    _t1_slicer[taxis] = slice(1, I.shape[taxis])
    _t1_slicer = tuple(_t1_slicer)
    _i_1 = I[_t1_slicer]
    _q_1 = Q[_t1_slicer]

    # Calculate phase shift info (trig identity for dividing complex numbers)
    _num = _i_1 * _q_0 - _q_1 * _i_0
    _den = _i_0 * _i_1 + _q_0 * _q_1

    # calculate moving of phase shift divisions
    _kshape = np.ones(len(I.shape), dtype=int)
    _kshape[kaxis] = ksize
    _kernel = np.ones(_kshape)/ksize
    if ksize > 1:
        from scipy.signal import fftconvolve
        _num = fftconvolve(_num, _kernel, mode='same', axes=kaxis)
        _den = fftconvolve(_den, _kernel, mode='same', axes=kaxis)
    
    # Convert scale phase if demodulation frequency is given
    disp = _scale * np.arctan2(_num, _den)

    if mode == 'cumsum':
        disp = np.cumsum(disp, axis=taxis)

    return disp