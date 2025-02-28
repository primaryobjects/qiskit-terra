# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""A module for visualizing device coupling maps"""

import math
from typing import List
import numpy as np
from qiskit.exceptions import QiskitError, MissingOptionalLibraryError
from .matplotlib import HAS_MATPLOTLIB
from .exceptions import VisualizationError
from .utils import matplotlib_close_if_inline


def plot_gate_map(
    backend,
    figsize=None,
    plot_directed=False,
    label_qubits=True,
    qubit_size=None,
    line_width=4,
    font_size=None,
    qubit_color=None,
    qubit_labels=None,
    line_color=None,
    font_color="w",
    ax=None,
    filename=None,
):
    """Plots the gate map of a device.

    Args:
        backend (BaseBackend): The backend instance that will be used to plot the device
            gate map.
        figsize (tuple): Output figure size (wxh) in inches.
        plot_directed (bool): Plot directed coupling map.
        label_qubits (bool): Label the qubits.
        qubit_size (float): Size of qubit marker.
        line_width (float): Width of lines.
        font_size (int): Font size of qubit labels.
        qubit_color (list): A list of colors for the qubits
        qubit_labels (list): A list of qubit labels
        line_color (list): A list of colors for each line from coupling_map.
        font_color (str): The font color for the qubit labels.
        ax (Axes): A Matplotlib axes instance.
        filename (str): file path to save image to.

    Returns:
        Figure: A Matplotlib figure instance.

    Raises:
        QiskitError: if tried to pass a simulator, or if the backend is None,
            but one of num_qubits, mpl_data, or cmap is None.
        MissingOptionalLibraryError: if matplotlib not installed.

    Example:
        .. jupyter-execute::
            :hide-code:
            :hide-output:

            from qiskit.test.ibmq_mock import mock_get_backend
            mock_get_backend('FakeVigo')

        .. jupyter-execute::

           from qiskit import QuantumCircuit, execute, IBMQ
           from qiskit.visualization import plot_gate_map
           %matplotlib inline

           provider = IBMQ.load_account()
           accountProvider = IBMQ.get_provider(hub='ibm-q')
           backend = accountProvider.get_backend('ibmq_vigo')
           plot_gate_map(backend)
    """
    if not HAS_MATPLOTLIB:
        raise MissingOptionalLibraryError(
            libname="Matplotlib",
            name="plot_gate_map",
            pip_install="pip install matplotlib",
        )

    if backend.configuration().simulator:
        raise QiskitError("Requires a device backend, not simulator.")

    qubit_coordinates_map = {}

    qubit_coordinates_map[1] = [[0, 0]]

    qubit_coordinates_map[5] = [[1, 0], [0, 1], [1, 1], [1, 2], [2, 1]]

    qubit_coordinates_map[7] = [[0, 0], [0, 1], [0, 2], [1, 1], [2, 0], [2, 1], [2, 2]]

    qubit_coordinates_map[20] = [
        [0, 0],
        [0, 1],
        [0, 2],
        [0, 3],
        [0, 4],
        [1, 0],
        [1, 1],
        [1, 2],
        [1, 3],
        [1, 4],
        [2, 0],
        [2, 1],
        [2, 2],
        [2, 3],
        [2, 4],
        [3, 0],
        [3, 1],
        [3, 2],
        [3, 3],
        [3, 4],
    ]

    qubit_coordinates_map[15] = [
        [0, 0],
        [0, 1],
        [0, 2],
        [0, 3],
        [0, 4],
        [0, 5],
        [0, 6],
        [1, 7],
        [1, 6],
        [1, 5],
        [1, 4],
        [1, 3],
        [1, 2],
        [1, 1],
        [1, 0],
    ]

    qubit_coordinates_map[16] = [
        [1, 0],
        [1, 1],
        [2, 1],
        [3, 1],
        [1, 2],
        [3, 2],
        [0, 3],
        [1, 3],
        [3, 3],
        [4, 3],
        [1, 4],
        [3, 4],
        [1, 5],
        [2, 5],
        [3, 5],
        [1, 6],
    ]

    qubit_coordinates_map[27] = [
        [1, 0],
        [1, 1],
        [2, 1],
        [3, 1],
        [1, 2],
        [3, 2],
        [0, 3],
        [1, 3],
        [3, 3],
        [4, 3],
        [1, 4],
        [3, 4],
        [1, 5],
        [2, 5],
        [3, 5],
        [1, 6],
        [3, 6],
        [0, 7],
        [1, 7],
        [3, 7],
        [4, 7],
        [1, 8],
        [3, 8],
        [1, 9],
        [2, 9],
        [3, 9],
        [3, 10],
    ]

    qubit_coordinates_map[28] = [
        [0, 2],
        [0, 3],
        [0, 4],
        [0, 5],
        [0, 6],
        [1, 2],
        [1, 6],
        [2, 0],
        [2, 1],
        [2, 2],
        [2, 3],
        [2, 4],
        [2, 5],
        [2, 6],
        [2, 7],
        [2, 8],
        [3, 0],
        [3, 4],
        [3, 8],
        [4, 0],
        [4, 1],
        [4, 2],
        [4, 3],
        [4, 4],
        [4, 5],
        [4, 6],
        [4, 7],
        [4, 8],
    ]

    qubit_coordinates_map[53] = [
        [0, 2],
        [0, 3],
        [0, 4],
        [0, 5],
        [0, 6],
        [1, 2],
        [1, 6],
        [2, 0],
        [2, 1],
        [2, 2],
        [2, 3],
        [2, 4],
        [2, 5],
        [2, 6],
        [2, 7],
        [2, 8],
        [3, 0],
        [3, 4],
        [3, 8],
        [4, 0],
        [4, 1],
        [4, 2],
        [4, 3],
        [4, 4],
        [4, 5],
        [4, 6],
        [4, 7],
        [4, 8],
        [5, 2],
        [5, 6],
        [6, 0],
        [6, 1],
        [6, 2],
        [6, 3],
        [6, 4],
        [6, 5],
        [6, 6],
        [6, 7],
        [6, 8],
        [7, 0],
        [7, 4],
        [7, 8],
        [8, 0],
        [8, 1],
        [8, 2],
        [8, 3],
        [8, 4],
        [8, 5],
        [8, 6],
        [8, 7],
        [8, 8],
        [9, 2],
        [9, 6],
    ]

    qubit_coordinates_map[65] = [
        [0, 0],
        [0, 1],
        [0, 2],
        [0, 3],
        [0, 4],
        [0, 5],
        [0, 6],
        [0, 7],
        [0, 8],
        [0, 9],
        [1, 0],
        [1, 4],
        [1, 8],
        [2, 0],
        [2, 1],
        [2, 2],
        [2, 3],
        [2, 4],
        [2, 5],
        [2, 6],
        [2, 7],
        [2, 8],
        [2, 9],
        [2, 10],
        [3, 2],
        [3, 6],
        [3, 10],
        [4, 0],
        [4, 1],
        [4, 2],
        [4, 3],
        [4, 4],
        [4, 5],
        [4, 6],
        [4, 7],
        [4, 8],
        [4, 9],
        [4, 10],
        [5, 0],
        [5, 4],
        [5, 8],
        [6, 0],
        [6, 1],
        [6, 2],
        [6, 3],
        [6, 4],
        [6, 5],
        [6, 6],
        [6, 7],
        [6, 8],
        [6, 9],
        [6, 10],
        [7, 2],
        [7, 6],
        [7, 10],
        [8, 1],
        [8, 2],
        [8, 3],
        [8, 4],
        [8, 5],
        [8, 6],
        [8, 7],
        [8, 8],
        [8, 9],
        [8, 10],
    ]

    config = backend.configuration()
    num_qubits = config.n_qubits
    coupling_map = config.coupling_map
    qubit_coordinates = qubit_coordinates_map.get(num_qubits)
    return plot_coupling_map(
        num_qubits,
        qubit_coordinates,
        coupling_map,
        figsize,
        plot_directed,
        label_qubits,
        qubit_size,
        line_width,
        font_size,
        qubit_color,
        qubit_labels,
        line_color,
        font_color,
        ax,
        filename,
    )


def plot_coupling_map(
    num_qubits: int,
    qubit_coordinates: List[List[int]],
    coupling_map: List[List[int]],
    figsize=None,
    plot_directed=False,
    label_qubits=True,
    qubit_size=None,
    line_width=4,
    font_size=None,
    qubit_color=None,
    qubit_labels=None,
    line_color=None,
    font_color="w",
    ax=None,
    filename=None,
):
    """Plots an arbitrary coupling map of qubits (embedded in a plane).

    Args:
        num_qubits (int): The number of qubits defined and plotted.
        qubit_coordinates (List[List[int]]): A list of two-element lists, with entries of each nested
            list being the planar coordinates in a 0-based square grid where each qubit is located.
        coupling_map (List[List[int]]): A list of two-element lists, with entries of each nested
            list being the qubit numbers of the bonds to be plotted.
        figsize (tuple): Output figure size (wxh) in inches.
        plot_directed (bool): Plot directed coupling map.
        label_qubits (bool): Label the qubits.
        qubit_size (float): Size of qubit marker.
        line_width (float): Width of lines.
        font_size (int): Font size of qubit labels.
        qubit_color (list): A list of colors for the qubits
        qubit_labels (list): A list of qubit labels
        line_color (list): A list of colors for each line from coupling_map.
        font_color (str): The font color for the qubit labels.
        ax (Axes): A Matplotlib axes instance.
        filename (str): file path to save image to.

    Returns:
        Figure: A Matplotlib figure instance.

    Raises:
        MissingOptionalLibraryError: if matplotlib not installed.
        QiskitError: If length of qubit labels does not match number of qubits.

    Example:
        .. jupyter-execute::
            :hide-code:
            :hide-output:

            from qiskit.test.ibmq_mock import mock_get_backend
            mock_get_backend('FakeVigo')

        .. jupyter-execute::

            from qiskit import QuantumCircuit, execute, IBMQ
            from qiskit.visualization import plot_coupling_map
            %matplotlib inline

            num_qubits = 8
            coupling_map = [[0, 1], [1, 2], [2, 3], [3, 5], [4, 5], [5, 6], [2, 4], [6, 7]]
            qubit_coordinates = [[0, 1], [1, 1], [1, 0], [1, 2], [2, 0],
                                 [2, 2], [2, 1], [3, 1]]
            plot_gate_map(num_qubits, coupling_map, qubit_coordinates)
    """

    if not HAS_MATPLOTLIB:
        raise MissingOptionalLibraryError(
            libname="Matplotlib",
            name="plot_coupling_map",
            pip_install="pip install matplotlib",
        )
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    input_axes = False
    if ax:
        input_axes = True

    if font_size is None:
        font_size = 12

    if qubit_size is None:
        qubit_size = 24
    if num_qubits > 20:
        qubit_size = 28
        font_size = 10

    if qubit_labels is None:
        qubit_labels = list(range(num_qubits))
    else:
        if len(qubit_labels) != num_qubits:
            raise QiskitError("Length of qubit labels does not equal number of qubits.")

    if qubit_coordinates is not None:
        grid_data = qubit_coordinates
    else:
        if not input_axes:
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.axis("off")
            if filename:
                fig.savefig(filename)
            return fig

    x_max = max(d[1] for d in grid_data)
    y_max = max(d[0] for d in grid_data)
    max_dim = max(x_max, y_max)

    if figsize is None:
        if num_qubits == 1 or (x_max / max_dim > 0.33 and y_max / max_dim > 0.33):
            figsize = (5, 5)
        else:
            figsize = (9, 3)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        ax.axis("off")

    # set coloring
    if qubit_color is None:
        qubit_color = ["#648fff"] * num_qubits
    if line_color is None:
        line_color = ["#648fff"] * len(coupling_map) if coupling_map else []

    # Add lines for couplings
    if num_qubits != 1:
        for ind, edge in enumerate(coupling_map):
            is_symmetric = False
            if edge[::-1] in coupling_map:
                is_symmetric = True
            y_start = grid_data[edge[0]][0]
            x_start = grid_data[edge[0]][1]
            y_end = grid_data[edge[1]][0]
            x_end = grid_data[edge[1]][1]

            if is_symmetric:
                if y_start == y_end:
                    x_end = (x_end - x_start) / 2 + x_start

                elif x_start == x_end:
                    y_end = (y_end - y_start) / 2 + y_start

                else:
                    x_end = (x_end - x_start) / 2 + x_start
                    y_end = (y_end - y_start) / 2 + y_start
            ax.add_artist(
                plt.Line2D(
                    [x_start, x_end],
                    [-y_start, -y_end],
                    color=line_color[ind],
                    linewidth=line_width,
                    zorder=0,
                )
            )
            if plot_directed:
                dx = x_end - x_start
                dy = y_end - y_start
                if is_symmetric:
                    x_arrow = x_start + dx * 0.95
                    y_arrow = -y_start - dy * 0.95
                    dx_arrow = dx * 0.01
                    dy_arrow = -dy * 0.01
                    head_width = 0.15
                else:
                    x_arrow = x_start + dx * 0.5
                    y_arrow = -y_start - dy * 0.5
                    dx_arrow = dx * 0.2
                    dy_arrow = -dy * 0.2
                    head_width = 0.2
                ax.add_patch(
                    mpatches.FancyArrow(
                        x_arrow,
                        y_arrow,
                        dx_arrow,
                        dy_arrow,
                        head_width=head_width,
                        length_includes_head=True,
                        edgecolor=None,
                        linewidth=0,
                        facecolor=line_color[ind],
                        zorder=1,
                    )
                )

    # Add circles for qubits
    for var, idx in enumerate(grid_data):
        _idx = [idx[1], -idx[0]]
        ax.add_artist(
            mpatches.Ellipse(
                _idx,
                qubit_size / 48,
                qubit_size / 48,  # This is here so that the changes
                color=qubit_color[var],
                zorder=1,
            )
        )  # to how qubits are plotted does
        if label_qubits:  # not affect qubit size kwarg.
            ax.text(
                *_idx,
                s=qubit_labels[var],
                horizontalalignment="center",
                verticalalignment="center",
                color=font_color,
                size=font_size,
                weight="bold",
            )
    ax.set_xlim([-1, x_max + 1])
    ax.set_ylim([-(y_max + 1), 1])
    ax.set_aspect("equal")

    if not input_axes:
        matplotlib_close_if_inline(fig)
        if filename:
            fig.savefig(filename)
        return fig
    return None


def plot_circuit_layout(circuit, backend, view="virtual"):
    """Plot the layout of a circuit transpiled for a given
    target backend.

    Args:
        circuit (QuantumCircuit): Input quantum circuit.
        backend (BaseBackend): Target backend.
        view (str): Layout view: either 'virtual' or 'physical'.

    Returns:
        Figure: A matplotlib figure showing layout.

    Raises:
        QiskitError: Invalid view type given.
        VisualizationError: Circuit has no layout attribute.

    Example:
        .. jupyter-execute::
            :hide-code:
            :hide-output:

            from qiskit.test.ibmq_mock import mock_get_backend
            mock_get_backend('FakeVigo')

        .. jupyter-execute::

            import numpy as np
            from qiskit import QuantumCircuit, IBMQ, transpile
            from qiskit.visualization import plot_histogram, plot_gate_map, plot_circuit_layout
            from qiskit.tools.monitor import job_monitor
            import matplotlib.pyplot as plt
            %matplotlib inline

            IBMQ.load_account()

            ghz = QuantumCircuit(3, 3)
            ghz.h(0)
            for idx in range(1,3):
                ghz.cx(0,idx)
            ghz.measure(range(3), range(3))

            provider = IBMQ.get_provider(hub='ibm-q')
            backend = provider.get_backend('ibmq_vigo')
            new_circ_lv3 = transpile(ghz, backend=backend, optimization_level=3)
            plot_circuit_layout(new_circ_lv3, backend)
    """
    if circuit._layout is None:
        raise QiskitError("Circuit has no layout. Perhaps it has not been transpiled.")

    num_qubits = backend.configuration().n_qubits

    qubits = []
    qubit_labels = [None] * num_qubits

    bit_locations = {
        bit: {"register": register, "index": index}
        for register in circuit._layout.get_registers()
        for index, bit in enumerate(register)
    }
    for index, qubit in enumerate(circuit._layout.get_virtual_bits()):
        if qubit not in bit_locations:
            bit_locations[qubit] = {"register": None, "index": index}

    if view == "virtual":
        for key, val in circuit._layout.get_virtual_bits().items():
            bit_register = bit_locations[key]["register"]
            if bit_register is None or bit_register.name != "ancilla":
                qubits.append(val)
                qubit_labels[val] = bit_locations[key]["index"]

    elif view == "physical":
        for key, val in circuit._layout.get_physical_bits().items():
            bit_register = bit_locations[val]["register"]
            if bit_register is None or bit_register.name != "ancilla":
                qubits.append(key)
                qubit_labels[key] = key

    else:
        raise VisualizationError("Layout view must be 'virtual' or 'physical'.")

    qcolors = ["#648fff"] * num_qubits
    for k in qubits:
        qcolors[k] = "k"

    cmap = backend.configuration().coupling_map

    lcolors = ["#648fff"] * len(cmap)

    for idx, edge in enumerate(cmap):
        if edge[0] in qubits and edge[1] in qubits:
            lcolors[idx] = "k"

    fig = plot_gate_map(backend, qubit_color=qcolors, qubit_labels=qubit_labels, line_color=lcolors)
    return fig


def plot_error_map(backend, figsize=(12, 9), show_title=True):
    """Plots the error map of a given backend.

    Args:
        backend (IBMQBackend): Given backend.
        figsize (tuple): Figure size in inches.
        show_title (bool): Show the title or not.

    Returns:
        Figure: A matplotlib figure showing error map.

    Raises:
        VisualizationError: Input is not IBMQ backend.
        VisualizationError: The backend does not provide gate errors for the 'sx' gate.
        MissingOptionalLibraryError: If seaborn is not installed

    Example:
        .. jupyter-execute::
            :hide-code:
            :hide-output:

            from qiskit.test.ibmq_mock import mock_get_backend
            mock_get_backend('FakeVigo')

        .. jupyter-execute::

            from qiskit import QuantumCircuit, execute, IBMQ
            from qiskit.visualization import plot_error_map
            %matplotlib inline

            IBMQ.load_account()
            provider = IBMQ.get_provider(hub='ibm-q')
            backend = provider.get_backend('ibmq_vigo')
            plot_error_map(backend)
    """
    try:
        import seaborn as sns
    except ImportError as ex:
        raise MissingOptionalLibraryError(
            libname="seaborn",
            name="plot_error_map",
            pip_install="pip install seaborn",
        ) from ex
    if not HAS_MATPLOTLIB:
        raise MissingOptionalLibraryError(
            libname="Matplotlib",
            name="plot_error_map",
            pip_install="pip install matplotlib",
        )
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import gridspec, ticker

    color_map = sns.cubehelix_palette(reverse=True, as_cmap=True)

    props = backend.properties().to_dict()
    config = backend.configuration().to_dict()

    num_qubits = config["n_qubits"]

    # sx error rates
    single_gate_errors = [0] * num_qubits
    for gate in props["gates"]:
        if gate["gate"] == "sx":
            _qubit = gate["qubits"][0]
            for param in gate["parameters"]:
                if param["name"] == "gate_error":
                    single_gate_errors[_qubit] = param["value"]
                    break
            else:
                raise VisualizationError(
                    f"Backend '{backend}' did not supply an error for the 'sx' gate."
                )

    # Convert to percent
    single_gate_errors = 100 * np.asarray(single_gate_errors)
    avg_1q_err = np.mean(single_gate_errors)

    single_norm = matplotlib.colors.Normalize(
        vmin=min(single_gate_errors), vmax=max(single_gate_errors)
    )
    q_colors = [color_map(single_norm(err)) for err in single_gate_errors]

    cmap = config["coupling_map"]

    directed = False
    line_colors = []
    if cmap:
        directed = False
        if num_qubits < 20:
            for edge in cmap:
                if not [edge[1], edge[0]] in cmap:
                    directed = True
                    break

        cx_errors = []
        for line in cmap:
            for item in props["gates"]:
                if item["qubits"] == line:
                    cx_errors.append(item["parameters"][0]["value"])
                    break
            else:
                continue

        # Convert to percent
        cx_errors = 100 * np.asarray(cx_errors)
        avg_cx_err = np.mean(cx_errors)

        cx_norm = matplotlib.colors.Normalize(vmin=min(cx_errors), vmax=max(cx_errors))
        line_colors = [color_map(cx_norm(err)) for err in cx_errors]

    # Measurement errors

    read_err = []

    for qubit in range(num_qubits):
        for item in props["qubits"][qubit]:
            if item["name"] == "readout_error":
                read_err.append(item["value"])

    read_err = 100 * np.asarray(read_err)
    avg_read_err = np.mean(read_err)
    max_read_err = np.max(read_err)

    fig = plt.figure(figsize=figsize)
    gridspec.GridSpec(nrows=2, ncols=3)

    grid_spec = gridspec.GridSpec(
        12, 12, height_ratios=[1] * 11 + [0.5], width_ratios=[2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2]
    )

    left_ax = plt.subplot(grid_spec[2:10, :1])
    main_ax = plt.subplot(grid_spec[:11, 1:11])
    right_ax = plt.subplot(grid_spec[2:10, 11:])
    bleft_ax = plt.subplot(grid_spec[-1, :5])
    if cmap:
        bright_ax = plt.subplot(grid_spec[-1, 7:])

    qubit_size = 28
    if num_qubits <= 5:
        qubit_size = 20
    plot_gate_map(
        backend,
        qubit_color=q_colors,
        line_color=line_colors,
        qubit_size=qubit_size,
        line_width=5,
        plot_directed=directed,
        ax=main_ax,
    )
    main_ax.axis("off")
    main_ax.set_aspect(1)
    if cmap:
        single_cb = matplotlib.colorbar.ColorbarBase(
            bleft_ax, cmap=color_map, norm=single_norm, orientation="horizontal"
        )
        tick_locator = ticker.MaxNLocator(nbins=5)
        single_cb.locator = tick_locator
        single_cb.update_ticks()
        single_cb.update_ticks()
        bleft_ax.set_title(f"H error rate (%) [Avg. = {round(avg_1q_err, 3)}]")

    if cmap is None:
        bleft_ax.axis("off")
        bleft_ax.set_title(f"H error rate (%) = {round(avg_1q_err, 3)}")

    if cmap:
        cx_cb = matplotlib.colorbar.ColorbarBase(
            bright_ax, cmap=color_map, norm=cx_norm, orientation="horizontal"
        )
        tick_locator = ticker.MaxNLocator(nbins=5)
        cx_cb.locator = tick_locator
        cx_cb.update_ticks()
        bright_ax.set_title(f"CNOT error rate (%) [Avg. = {round(avg_cx_err, 3)}]")

    if num_qubits < 10:
        num_left = num_qubits
        num_right = 0
    else:
        num_left = math.ceil(num_qubits / 2)
        num_right = num_qubits - num_left

    left_ax.barh(range(num_left), read_err[:num_left], align="center", color="#DDBBBA")
    left_ax.axvline(avg_read_err, linestyle="--", color="#212121")
    left_ax.set_yticks(range(num_left))
    left_ax.set_xticks([0, round(avg_read_err, 2), round(max_read_err, 2)])
    left_ax.set_yticklabels([str(kk) for kk in range(num_left)], fontsize=12)
    left_ax.invert_yaxis()
    left_ax.set_title("Readout Error (%)", fontsize=12)

    for spine in left_ax.spines.values():
        spine.set_visible(False)

    if num_right:
        right_ax.barh(
            range(num_left, num_qubits), read_err[num_left:], align="center", color="#DDBBBA"
        )
        right_ax.axvline(avg_read_err, linestyle="--", color="#212121")
        right_ax.set_yticks(range(num_left, num_qubits))
        right_ax.set_xticks([0, round(avg_read_err, 2), round(max_read_err, 2)])
        right_ax.set_yticklabels([str(kk) for kk in range(num_left, num_qubits)], fontsize=12)
        right_ax.invert_yaxis()
        right_ax.invert_xaxis()
        right_ax.yaxis.set_label_position("right")
        right_ax.yaxis.tick_right()
        right_ax.set_title("Readout Error (%)", fontsize=12)
    else:
        right_ax.axis("off")

    for spine in right_ax.spines.values():
        spine.set_visible(False)

    if show_title:
        fig.suptitle(f"{backend.name()} Error Map", fontsize=24, y=0.9)
    matplotlib_close_if_inline(fig)
    return fig
