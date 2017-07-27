from __future__ import print_function
import numpy as np
import copy 
from bokeh.plotting import Figure
from bokeh.models import ColumnDataSource, HoverTool, Range1d 
from bokeh.layouts import Column, Row, WidgetBox
from bokeh.models.widgets import Slider, TextInput, Select, Tabs, Panel, Div 
from bokeh.io import curdoc
from bokeh.models.callbacks import CustomJS
import astropy.constants as const
import get_lumos_spectra
import Telescope as T 
import lumos_help as h 


luvoir = T.Telescope(15., 280., 500.) # set up LUVOIR with 15 meters, T = 280, and diff limit at 500 nm 
lumos = T.Spectrograph() # set up LUVOIR with 10 meters, T = 280, and diff limit at 500 nm 
lumos.set_mode('G120M') 

def simulate_exposure(telescope, spectrograph, wave, flux, exptime): 
    print("Attempting to create an exposure for Telescope: ", telescope.name, telescope.aperture, ' m') 
    print("                                 and Spectrograph: ", spectrograph.name, " in mode ", spectrograph.mode_name) 

    # obtain the interpolated effective areas for the input spectrum 
    aeff_interp = np.interp(wave, spectrograph.wave, spectrograph.aeff, left=0., right=0.) * (telescope.aperture/15.)**2 
    bef_interp = np.interp(wave, spectrograph.wave, spectrograph.bef, left=0., right=0.) # background to use 
    phot_energy = const.h.to('erg s').value * const.c.to('cm/s').value / (wave * 1e-8) # now convert from erg cm^-2 s^-1 A^-1  
    source_counts = flux / phot_energy * aeff_interp * (exptime*3600.) * (wave / lumos.R) 

    source_counts[(wave < spectrograph.lambda_range[0])] = 0. 
    source_counts[(wave > spectrograph.lambda_range[1])] = 0. 

    background_counts = bef_interp / phot_energy * aeff_interp * (exptime*3600.) * (wave / lumos.R) 
    signal_to_noise = source_counts / (source_counts + background_counts)** 0.5 
    for sdf in signal_to_noise: print(sdf) 
    return signal_to_noise 

##### START FOR NEW WAY TO GET TEMPLATE SPECTRA 
spec_dict = get_lumos_spectra.add_spectrum_to_library() 
template_to_start_with = 'QSO' 
spec_dict[template_to_start_with].wave 
spec_dict[template_to_start_with].flux # <---- these are the variables you need 

signal_to_noise = simulate_exposure(luvoir, lumos, spec_dict[template_to_start_with].wave, spec_dict[template_to_start_with].flux, 1.0) 

flux_cut = spec_dict[template_to_start_with].flux 
flux_cut[spec_dict[template_to_start_with].wave < lumos.lambda_range[0]] = -999.  
flux_cut[spec_dict[template_to_start_with].wave > lumos.lambda_range[0]] = -999.  

spectrum_template = ColumnDataSource(data=dict(w=spec_dict[template_to_start_with].wave, f=spec_dict[template_to_start_with].flux, \
                                   w0=spec_dict[template_to_start_with].wave, f0=spec_dict[template_to_start_with].flux, \
                                   flux_cut=flux_cut, sn=signal_to_noise)) 

instrument_info = ColumnDataSource(data=dict(wave=lumos.wave, bef=lumos.bef))

# set up the flux plot 
flux_plot = Figure(plot_height=400, plot_width=800, 
              tools="crosshair,hover,pan,reset,save,box_zoom,wheel_zoom", outline_line_color='black', 
              x_range=[900, 2000], y_range=[0, 4e-16], toolbar_location='right') 
flux_plot.x_range=Range1d(900,4000,bounds=(900,4000))
flux_plot.y_range=Range1d(0,4e-16,bounds=(0,None)) 
flux_plot.background_fill_color = "beige"
flux_plot.background_fill_alpha = 0.5 
flux_plot.yaxis.axis_label = 'Flux [erg / s / cm2 / Ang]' 
flux_plot.xaxis.axis_label = 'Wavelength [Angstrom]' 
flux_plot.line('w', 'f', source=spectrum_template, line_width=3, line_color='firebrick', line_alpha=0.7, legend='Source Flux')
flux_plot.line('wave', 'bef', source=instrument_info, line_width=3, line_color='darksalmon', line_alpha=0.7, legend='Background')

# set up the flux plot 
sn_plot = Figure(plot_height=400, plot_width=800, 
              tools="crosshair,hover,pan,reset,save,box_zoom,wheel_zoom", outline_line_color='black', 
              x_range=[900, 2000], y_range=[0, 40], toolbar_location='right')
sn_plot.x_range=Range1d(900,4000,bounds=(900,4000))
sn_plot.y_range=Range1d(0,40,bounds=(0,None)) 
sn_plot.line('w', 'sn', source=spectrum_template, line_width=3, line_color='orange', line_alpha=0.7, legend='S/N per resel')
sn_plot.background_fill_color = "beige"
sn_plot.background_fill_alpha = 0.5 
sn_plot.xaxis.axis_label = 'Wavelength [Angstrom]' 
sn_plot.yaxis.axis_label = 'S/N per resel' 

def update_data(attrname, old, new): # use this one for updating pysynphot tempaltes 
   
    print("You have chosen template ", template.value, np.size(spec_dict[template.value].wave)) 
    print('Selected grating = ', grating.value) 
    luvoir.aperture = aperture.value 
    print('Your telescope is set to', luvoir.aperture) 
    lumos.set_mode(grating.value) 

    new_w0 = spec_dict[template.value].wave 
    new_f0 = spec_dict[template.value].flux 
 
    #OOPS, SHOULD USE PYSYNPHOT FOR REDSHIFT HERE, THE NORMALIZATION IS NOT QUITE CORRECT 
    new_w = np.array(new_w0) * (1. + redshift.value)
    new_f = np.array(new_f0) * 10.**( (21.-magnitude.value) / 2.5)
    new_sn = np.nan_to_num(simulate_exposure(luvoir, lumos, new_w, new_f, exptime.value)) 

    flux_cut = copy.deepcopy(new_f) 
    flux_cut[new_w < lumos.lambda_range[0]] = -999.  
    flux_cut[new_w > lumos.lambda_range[1]] = -999.  
    print('RANGE', lumos.lambda_range[0], lumos.lambda_range[1]) 

    new_dict = {'w':new_w, 'f':new_f, 'w0':new_w0, 'f0':new_f0, 'flux_cut':flux_cut, 'sn':new_sn} 
    spectrum_template.data = new_dict 

    # set the axes to autoscale appropriately 
    flux_plot.y_range.start = 0 
    flux_plot.y_range.end = 1.5*np.max(new_f0)
    sn_plot.y_range.start = 0 
    sn_plot.y_range.end = 1.3*np.max(spectrum_template.data['sn'])
    print('MAX MAX', np.max(spectrum_template.data['f']), np.max(flux_cut)) 

    instrument_info.data['wave'] = lumos.wave 
    instrument_info.data['bef'] = lumos.bef  

# fake source for managing callbacks 
source = ColumnDataSource(data=dict(value=[]))
source.on_change('data', update_data)

# Set up widgets and their callbacks (faking the mouseup policy via "source" b/c functional callback doesn't do that. 
template = Select(title="Template Spectrum", value="QSO", 
                options=["Flat in F_lambda", "QSO", "10 Myr Starburst", "O5V Star", "G2V Star", "G191B2B (WD)", "GD71 (WD)", "GD153 (WD)", "Classical T Tauri", "M1 Dwarf", "Orion Nebula", \
                         "Starburst, No Dust", "Starburst, E(B-V) = 0.6", "Galaxy with f_esc, HI=1, HeI=1", "Galaxy with f_esc, HI=0.001, HeI=1"])

redshift = Slider(title="Redshift", value=0.0, start=0., end=3.0, step=0.05, callback_policy='mouseup')
redshift.callback = CustomJS(args=dict(source=source), code="""
    source.data = { value: [cb_obj.value] }
""")
magnitude = Slider(title="Magnitude [AB]", value=21., start=15., end=30.0, step=0.1, callback_policy='mouseup')
magnitude.callback = CustomJS(args=dict(source=source), code="""
    source.data = { value: [cb_obj.value] }
""")
grating = Select(title="Grating / Setting", value="G120M (R = 30,000)", \
                 options=["G120M (R = 30,000)", "G150M (R = 30,000)", "G180M (R = 30,000)", "G155L (R = 5,000)", "G300M (R = 30000)"])
aperture= Slider(title="Aperture (meters)", value=15., start=2., end=20.0, step=1.0, callback_policy='mouseup')
aperture.callback = CustomJS(args=dict(source=source), code="""
    source.data = { value: [cb_obj.value] }
""")
exptime = Slider(title="Exposure Time [hr]", value=1.0, start=0.1, end=10.0, step=0.1, callback_policy='mouseup')
exptime.callback = CustomJS(args=dict(source=source), code="""
    source.data = { value: [cb_obj.value] }
""")

# iterate on changes to parameters 
for w in [template, grating]:  w.on_change('value', update_data)
 
# Set up layouts and add to document
source_inputs = WidgetBox(children=[template, redshift, magnitude])
controls_tab = Panel(child=source_inputs, title='Controls')
help = Div(text = h.help()) 
help_tab = Panel(child=help, title='Info')
source_inputs = Tabs(tabs=[ controls_tab, help_tab]) 

exposure_inputs = WidgetBox(children=[grating, aperture, exptime])


row1 = Row(children=[source_inputs, flux_plot])
row2 = Row(children=[exposure_inputs, sn_plot])

curdoc().add_root(Column(children=[row1, row2]))
curdoc().add_root(source) 





