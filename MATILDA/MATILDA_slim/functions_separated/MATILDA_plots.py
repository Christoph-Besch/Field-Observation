import matplotlib.pyplot as plt

# Plotting the meteorological parameters
def plot_meteo(plot_data, freq_long=''):
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True, figsize=(10,6))
    ax1.plot(plot_data.index.to_pydatetime(), (plot_data["T2"]), c="#d7191c")
    ax2.bar(plot_data.index.to_pydatetime(), plot_data["RRR"], width=10, color="#2c7bb6")
    ax3.plot(plot_data.index.to_pydatetime(), plot_data["PE"], c="#008837")
    plt.xlabel("Date", fontsize=9)
    ax1.grid(linewidth=0.25), ax2.grid(linewidth=0.25), ax3.grid(linewidth=0.25)
    ax1.set_title("Mean temperature", fontsize=9)
    ax2.set_title("Precipitation sum", fontsize=9)
    ax3.set_title("Evapotranspiration sum", fontsize=9)
    ax1.set_ylabel("[°C]", fontsize=9)
    ax2.set_ylabel("[mm]", fontsize=9)
    ax3.set_ylabel("[mm]", fontsize=9)
    if str(plot_data.index.values[1])[:4] == str(plot_data.index.values[-1])[:4]:
        fig.suptitle(freq_long + " meteorological input parameters in " + str(plot_data.index.values[-1])[:4],
                     size=14)
    else:
        fig.suptitle(freq_long + " meteorological input parameters in " + str(plot_data.index.values[1])[
                                                                                    :4] + "-" + str(
            plot_data.index.values[-1])[:4], size=14)
    plt.tight_layout()
    fig.set_size_inches(10, 6)
    return fig

def plot_runoff(plot_data, freq_long='', nash_sut=None):
    plot_data["plot"] = 0
    fig = plt.figure(figsize=(10, 6))
    if 'Qobs' in plot_data:
        plt.plot(plot_data.index.to_pydatetime(), plot_data["Qobs"], c="#E69F00", label="Observations", linewidth=1.2)
    plt.plot(plot_data.index.to_pydatetime(), plot_data["Q_Total"], c="k", label="MATILDA total runoff",
             linewidth=0.75, alpha=0.75)
    plt.fill_between(plot_data.index.to_pydatetime(), plot_data["plot"], plot_data["Q_HBV"], color='#56B4E9',
                     alpha=.75, label="MATILDA catchment runoff")
    plt.fill_between(plot_data.index.to_pydatetime(), plot_data["Q_HBV"], plot_data["Q_Total"],
                     color='#CC79A7', alpha=.75, label="MATILDA glacial runoff")
    plt.legend()
    plt.ylabel("Runoff [mm]", fontsize=9)
    if str(plot_data.index.values[1])[:4] == str(plot_data.index.values[-1])[:4]:
        plt.title(freq_long + " MATILDA simulation for the period "+ str(plot_data.index.values[-1])[:4],
                     size=14)
    else:
        plt.title(freq_long + " MATILDA simulation for the period "+ str(plot_data.index.values[1])[
                                                                                    :4] + "-" + str(
            plot_data.index.values[-1])[:4], size=14)
    if nash_sut == "error":
            plt.text(0.77, 0.9, 'NS coeff exceeds boundaries', fontsize=8, transform=fig.transFigure)
    elif isinstance(nash_sut, float):
            plt.text(0.85, 0.9, 'NS coeff ' + str(round(nash_sut, 2)), fontsize=8, transform=fig.transFigure)
    plt.tight_layout()
    fig.set_size_inches(10, 6)
    return fig


# Plotting the HBV output parameters
def plot_hbv(plot_data, freq_long=''):
    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, sharex=True, figsize=(10,6))
    ax1.plot(plot_data.index.to_pydatetime(), plot_data["HBV_AET"], "k")
    ax2.plot(plot_data.index.to_pydatetime(), plot_data["HBV_soil_moisture"], "k")
    ax3.plot(plot_data.index.to_pydatetime(), plot_data["HBV_snowpack"], "k")
    ax4.plot(plot_data.index.to_pydatetime(), plot_data["HBV_upper_gw"], "k")
    ax5.plot(plot_data.index.to_pydatetime(), plot_data["HBV_lower_gw"], "k")
    ax1.set_title("Actual evapotranspiration", fontsize=9)
    ax2.set_title("Soil moisture", fontsize=9)
    ax3.set_title("Water in snowpack", fontsize=9)
    ax4.set_title("Upper groundwater box", fontsize=9)
    ax5.set_title("Lower groundwater box", fontsize=9)
    plt.xlabel("Date", fontsize=9)
    ax1.set_ylabel("[mm]", fontsize=9), ax2.set_ylabel("[mm]", fontsize=9), ax3.set_ylabel("[mm]", fontsize=9)
    ax4.set_ylabel("[mm]", fontsize=9), ax5.set_ylabel("[mm]", fontsize=9)
    if str(plot_data.index.values[1])[:4] == str(plot_data.index.values[-1])[:4]:
        fig.suptitle(freq_long + " output from the HBV model in the period "+ str(plot_data.index.values[-1])[:4],
                     size=14)
    else:
        fig.suptitle(freq_long + " output from the HBV model in the period "+ str(plot_data.index.values[1])[
                                                                                    :4] + "-" + str(
            plot_data.index.values[-1])[:4], size=14)
    plt.tight_layout()
    fig.set_size_inches(10, 6)
    return fig

def MATILDA_plots(output_MATILDA, parameter):
    freq_long = parameter.freq_long
    fig1 = plot_meteo(output_MATILDA[0], freq_long=freq_long)
    fig2 = plot_runoff(output_MATILDA[0], freq_long=freq_long, nash_sut=output_MATILDA[1])
    fig3 = plot_hbv(output_MATILDA[0], freq_long=freq_long)
    output_MATILDA.extend([fig1, fig2, fig3])
    return output_MATILDA
