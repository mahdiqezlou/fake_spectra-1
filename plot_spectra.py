# -*- coding: utf-8 -*-
"""Contains the plotting-specific functions for the spectrum analysis code."""

import spectra
import halospectra
import numpy as np
import math
import leastsq as lsq
import kstest as ks
import matplotlib.pyplot as plt

class PlottingSpectra(spectra.Spectra):
    """Class to plot things connected with spectra."""
    def __init__(self,num, base, cofm=None, axis=None, res=1., savefile="grid_spectra_DLA.hdf5",label="", snr=0., spec_res = 8., cdir=None):
        spectra.Spectra.__init__(self,num, base, cofm, axis, res, savefile=savefile, snr=snr, spec_res=spec_res, cdir=cdir)
        self.label=label

    def plot_vel_width(self, elem, ion, dv=0.1, color="red", ls="-"):
        """Plot the velocity widths of this snapshot
        Parameters:
            elem - element to use
            ion - ionisation state: 1 is neutral.
            dv - bin spacing
        """
        (vbin, vels) = self.vel_width_hist(elem, ion, dv)
        plt.semilogx(vbin, vels, color=color, lw=3, ls=ls,label=self.label)

    def plot_eq_width(self, elem, ion, line, dv=0.1, eq_cut = 0.002, color="red", ls="-"):
        """Plot the velocity widths of this snapshot
        Parameters:
            elem - element to use
            ion - ionisation state: 1 is neutral.
            line - line number to use
            dv - bin spacing
        """
        (vbin, eqw) = self.eq_width_hist(elem, ion, line, dv, eq_cut=eq_cut)
        plt.plot(vbin, eqw, color=color, lw=3, ls=ls,label=self.label)

    def plot_f_meanmedian(self, elem, ion, dv=0.03, color="red", ls="-"):
        """
        Plot an f_mean_median histogram
        For args see plot_vel_width
        """
        (vbin, vels) = self.f_meanmedian_hist(elem, ion, dv)
        plt.plot(vbin, vels, color=color, lw=3, ls=ls,label=self.label)
        plt.xlabel(r"$f_\mathrm{mm}$")

    def _get_vamp(self, elem, ion, thresh=10**19):
        """Get the total amplitude of the velocity in the LLS pixels"""
        velocity = self.get_velocity(elem, ion)
        colden = self.get_col_density(elem, ion)
        (halo, _) = self.find_nearest_halo()
        #Subtract velocity at peak density
        mvamp = []
        vvir = self.virial_vel(halo)
        for ii in xrange(self.NumLos):
            if halo[ii] < 0 or vvir[ii] == 0.:
                continue
            ind = np.where(colden[ii,:] >= thresh)
            #Position of the point
            proj_pos = self.cofm[ii,:] - self.sub_cofm[halo[ii]]
            ax = self.axis[ii]-1
            axpos = ind*self.box/self.nbins - self.sub_cofm[halo[ii]][ax]
            lvel =  velocity[ii, :,:] - self.sub_vel[halo[ii]]
            vamp = np.sqrt(np.sum(lvel[ind,:][0]**2,axis=1))
            for ee in xrange(np.size(ind[0])):
                axpos = np.array(proj_pos)
                axpos[ax] = ind[0][ee]*self.box/self.nbins - self.sub_cofm[halo[ii]][ax]
                vamp[ee] /= np.sqrt(np.sum(axpos**2))
            angvir = vvir[ii] / self.sub_radii[halo[ii]]
            mvamp = np.append(mvamp, vamp/angvir)
        return mvamp

    def plot_velocity_amp(self,elem, ion, color="blue", ls="-"):
        """Plot a histogram of the amplitude of the velocity."""
        v_table = np.arange(0, 10, 0.2)
        (vbin, vels) = self._vel_stat_hist(elem, ion, v_table, self._get_vamp, log=False, filt=False)
        plt.plot(vbin, vels, label=self.label, color=color, ls=ls)
        plt.xlabel(r"$|v|$ (km s$^{-1}$)")
        plt.ylim(0,0.4)

    def plot_f_peak(self, elem, ion, dv=0.03, color="red", ls="-"):
        """
        Plot an f_peak histogram
        For args see plot_vel_width
        """
        (vbin, vels) = self.f_peak_hist(elem, ion, dv)
        plt.plot(vbin, vels, color=color, lw=3, ls=ls,label=self.label)
        plt.xlabel(r"$f_\mathrm{edg}$")

    def plot_spectrum(self, elem, ion, line, num, flux=True):
        """Plot an spectrum, centered on the maximum tau,
           and marking the 90% velocity width.
           offset: offset in km/s for the x-axis labels"""
        if line == -1:
            tau = self.get_observer_tau(elem, ion, num)
        else:
            tau = self.get_tau(elem, ion, line, num)
        (low, high, offset) = self.find_absorber_width(elem, ion)
        tau = np.roll(tau, offset[num])
        return self.plot_spectrum_raw(tau[low[num]:high[num]], flux)

    def plot_spectrum_raw(self, tau, flux=True):
        """Plot an array of optical depths, centered on the largest point,
           and marking the 90% velocity width.
           offset: offset in km/s for the x-axis labels"""
        (low, high) = self._vel_width_bound(tau)
        xaxis = np.arange(0,np.size(tau))*self.dvbin - (high+low)/2
        #Make sure we were handed a single spectrum
        assert np.size(np.shape(tau)) == 1
        if flux:
            plt.plot(xaxis,np.exp(-tau))
        else:
            plt.plot(xaxis,tau)
        if high - low > 0:
            plt.plot([xaxis[0]+low,xaxis[0]+low],[-1,20])
            plt.plot([xaxis[0]+high,xaxis[0]+high],[-1,20])
        if high - low > 150:
            tpos = xaxis[0]+low + 15
        else:
            tpos = xaxis[0]+high+15
        plt.text(tpos,0.5,r"$\delta v_{90} = "+str(np.round(high-low,1))+r"$")
        plt.xlim(np.max((xaxis[0],xaxis[0]+low-50)),np.min((xaxis[-1],xaxis[0]+high+50)))
#         plt.xlim(xaxis[0],xaxis[-1])
        plt.xlabel(r"v (km s$^{-1}$)")
        if flux:
            plt.ylabel(r"$\mathcal{F}$")
            plt.ylim(-0.05,1.05)
        else:
            plt.ylabel(r"$\tau$")
            plt.ylim(-0.1,np.min((np.max(tau)+0.2,10)))
        return xaxis[0] #(xaxis[0]+low, xaxis[0]+high)

    def plot_density(self, elem, ion, num):
        """Plot the density of an ion along a sightline"""
        den = self.get_density(elem, ion)
        mcol = np.max(den[num])
        ind_m = np.where(den[num] == mcol)[0][0]
        den = np.roll(den[num], np.size(den[num])/2 - ind_m)
        phys = self.dvbin/self.velfac
        #Add one to avoid zeros on the log plot
        plt.semilogy(np.arange(0,np.size(den))*phys-np.size(den)/2*phys,den+1e-30)
        plt.xlabel(r"x (kpc h$^{-1}$)")
        plt.ylabel(r"n (cm$^{-3}$)")

    def plot_den_to_tau(self, elem, ion, num, thresh = 1e-10,xlim=100, voff = 0.):
        """Make a plot connecting density on the low x axis to optical depth on the high x axis.
        Arguments:
            elem, ion - ionic species to plot
            num - index of spectrum shown
            thresh - density threshold above with to track the pixels
            xlim - width of shown plot in km/s
            voff - constant value to shift the high x axis by."""
        #Number of points to draw for each line
        npix = 10
        #Get densities above threshold
        den = self.get_density(elem, ion)[num]
        imax = np.where(den == np.max(den))[0][0]
        ind = np.where(den > thresh)
        #Get peculiar velocity along sightline
        ax = self.axis[num]-1
        vel = self.get_velocity(elem, ion)[num, :, ax]
        #Adjust the axis offset.
        vel -= vel[imax]-voff
        #Convert pixel coordinates to offsets from peak
        ind = np.ravel(ind)
        coord = (ind - imax)*self.dvbin
        coord[np.where(coord > self.nbins/2)] = coord - self.nbins
        coord[np.where(coord < -self.nbins/2)] = coord + self.nbins
        #For each pixel
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twiny()
        for (cc, ii) in zip(coord, ind):
            x = cc+np.linspace(0,vel[ii], npix)
            y = np.linspace(0,1,npix)
            ax2.plot(x,y,ls="-", color="black")
            ax1.plot(x/self.velfac,y,ls=".")
        ax2.set_xlabel(r"km s$^{-1}$")
        ax1.set_xlabel(r"kpc h$^{-1}$")
        #Very important to update both axes limits for this plot to make sense
        ax2.set_xlim(-1.*xlim, xlim)
        ax1.set_xlim(-1.*xlim/self.velfac, xlim/self.velfac)
        plt.ylim(0,1)
        plt.yticks(())
        return (ax1, ax2)

    def plot_temp(self, elem, ion):
        """Make a contour plot for the density weighted temperature for each spectrum"""
        temp = self.get_temp(elem, ion)
        den = self.get_density(elem, ion)
        ind = np.where(den < 1e-6)
        den[ind] = 0.
        temps = np.sum(temp*den, axis=1)/np.sum(den, axis=1)
        ind2 = np.where(temps < 1e5)
        print np.median(temps)," filt: ", np.median(temps[ind2])
        self._plot_2d_contour(np.sum(den,axis=1)[ind2], temps[ind2], 40, name="Temp Density", color="blue", color2="darkblue", ylog=False, xlog=True, fit=False, sample = 300)
        plt.xlabel(r"n (cm$^{-3}$)")
        plt.ylabel(r"T (K)")
        plt.ylim(0,2e4)

    def plot_cddf(self,elem = "H", ion = 1, dlogN=0.2, minN=13, maxN=23., color="blue", moment=False):
        """Plots the column density distribution function. """
        (NHI,f_N)=self.column_density_function(elem, ion, dlogN,minN-1,maxN+1)
        if moment:
            f_N *= NHI
        plt.loglog(NHI,f_N,color=color, lw = 3)
        ax=plt.gca()
        ax.set_xlabel(r"$N_\mathrm{HI} (\mathrm{cm}^{-2})$")
        ax.set_ylabel(r"$f(N) (\mathrm{cm}^2)$")
        plt.xlim(10**minN, 10**maxN)
        if moment:
            plt.ylim(1e-4,1)

    def plot_sep_frac(self,elem = "Si", ion = 2, thresh = 1e-1, mindist = 15, dv = 0.2, color="blue", ls="-"):
        """
        Plots the fraction of spectra in each velocity width bin which are separated.
        Threshold is as a percentage of the maximum value.
        mindist is in km/s
        """
        sep = self.get_separated(elem, ion, thresh,mindist)
        vels = self.vel_width(elem, ion)
        ind = self.get_filt(elem, ion)
        v_table = 10**np.arange(1, 3, dv)
        vbin = np.array([(v_table[i]+v_table[i+1])/2. for i in range(0,np.size(v_table)-1)])
        hist1 = np.histogram(vels[ind], v_table)
        hist2 = np.histogram(vels[ind][sep],v_table)
        hist1[0][np.where(hist1[0] == 0)] = 1
        plt.semilogx(vbin, hist2[0]/(1.*hist1[0]), color=color, ls=ls, label=self.label)

    def plot_vel_width_breakdown(self, elem = "Si", ion = 2, dv = 0.1):
        """
        Plots the fraction of the total velocity width histogram in a series of virial velocity bins
        """
        #Find velocity width
        vels = self.vel_width(elem, ion)
        ii = self.get_filt(elem, ion)
        self._plot_breakdown(vels,ii,(0, 60, 120), (60, 120, 900), ("< 60", "60-120", "> 120"),dv)
        plt.xlabel(r"$v_\mathrm{90}$ (km s$^{-1}$)")
        plt.ylim(0,1)


    def plot_f_peak_breakdown(self, elem = "Si", ion = 2, dv = 0.05):
        """
        Plots the fraction of the total fedge histogram in a series of virial velocity bins
        """
        #Find velocity width
        vels = self.vel_peak(elem, ion)
        ii = self.get_filt(elem, ion)
        self._plot_breakdown(vels,ii,(0, 50), (50, 900), ("< 50", "> 50"),dv, False)
        plt.xlabel(r"$f_\mathrm{edg}$")
        plt.ylim(0,1)
        plt.xlim(0,1)
        plt.legend(loc=1,ncol=2)

    def _plot_breakdown(self, array, filt, low, high, labels, dv, log=True):
        """
        Helper function to plot something broken down by halo mass
        """
        #Find virial velocity
        (halo, _) = self.find_nearest_halo()
        ind = np.where(halo[filt] > 0)
        virial = self.virial_vel(halo[filt][ind])
        array = array[filt]
        #Make bins
        if log:
            func = plt.semilogx
            v_table = 10**np.arange(np.min(np.log10(array)),np.max(np.log10(array)) , dv)
        else:
            func = plt.plot
            v_table = np.arange(np.min(array),np.max(array) , dv)
        vbin = np.array([(v_table[i]+v_table[i+1])/2. for i in range(0,np.size(v_table)-1)])
        #Histogram of vel width
        vhist = np.histogram(array, v_table)[0]
        vhist[np.where(vhist == 0)] = 1
        colors = ("red", "purple", "cyan")
        lss = ("--", ":", "-")
        #Histogram of vel width for all halos in given virial velocity bin
        for ii in xrange(len(low)):
            vind = np.where((virial > low[ii])*(virial < high[ii]))
            vhist2 = np.histogram(array[ind][vind], v_table)[0]
            func(vbin, vhist2/(1.*vhist), color=colors[ii], ls=lss[ii], label=labels[ii])
#         vind = np.where(halo[filt] < 0)
#         vhist2 = np.histogram(array[vind], v_table)[0]
#         func(vbin, vhist2/(1.*vhist), color="grey", ls="-.", label="Field")

    def plot_mult_halo_frac(self,elem = "Si", ion = 2, dv = 0.2, color="blue", ls="-"):
        """
        Plots the fraction of spectra in each velocity width bin which are separated.
        Threshold is as a percentage of the maximum value.
        mindist is in km/s
        """
        #Find velocity width
        (halos, subhalos) = self.find_nearby_halos()
        vels = self.vel_width(elem, ion)
        ii = self.get_filt(elem, ion)
        #Find virial velocity
        (halo, _) = self.find_nearest_halo()
        ind = np.where(halo[ii] > 0)
#         virial = np.ones_like(halo, dtype=np.double)
#         virial[ind] = self.virial_vel(halo[ind])
        vwvir = vels[ii][ind]  #/virial[ind]
        #Make bins
        v_table = 10**np.arange(np.min(np.log10(vwvir)),np.max(np.log10(vwvir)) , dv)
        vbin = np.array([(v_table[i]+v_table[i+1])/2. for i in range(0,np.size(v_table)-1)])
        #Histogram of vel width / virial vel
        hist1 = np.histogram(vwvir, v_table)
        hist1[0][np.where(hist1[0] == 0)] = 1
        #Find places with multiple halos
        subhalo_parent = [list(self.sub_sub_index[ss]) for ss in subhalos]
        allh = np.array([list(set(subhalo_parent[ii] + halos[ii])) for ii in xrange(self.NumLos)])
        indmult = np.where([len(aa) > 1 for aa in allh[ind]])
        histmult = np.histogram(vwvir[indmult],v_table)
        plt.semilogx(vbin, histmult[0]/(1.*hist1[0]), color=color, ls=ls, label=self.label)

    def _plot_metallicity(self, met, nbins=20,color="blue", ls="-"):
        """Plot the distribution of metallicities"""
        bins=np.linspace(-3,0,nbins)
        mbin = np.array([(bins[i]+bins[i+1])/2. for i in range(0,np.size(bins)-1)])
        #Abs. distance for entire spectrum
        hist = np.histogram(np.log10(met),bins,density=True)[0]
        plt.plot(mbin,hist,color=color,label=self.label,ls=ls)

    def plot_metallicity(self, nbins=20,color="blue", ls="-"):
        """Plot the distribution of metallicities"""
        met = self.get_metallicity()
        self._plot_metallicity(met,nbins,color,ls)

    def plot_species_metallicity(self, species, ion, nbins=20,color="blue", ls="-"):
        """Plot the distribution of metallicities from an ionic species"""
        met = self.get_ion_metallicity(species,ion)
        self._plot_metallicity(met,nbins,color,ls)

    def plot_ion_corr(self, species, ion, nbins=80,color="blue",ls="-"):
        """Plot the difference between the single-species ionisation and the metallicity from GFM_Metallicity"""
        met = np.log10(self.get_metallicity())
        ion_met = np.log10(self.get_ion_metallicity(species, ion))
        diff = 10**(ion_met - met)
        print np.max(diff), np.min(diff), np.median(diff)
        bins=np.linspace(-1,1,nbins)
        mbin = np.array([(bins[i]+bins[i+1])/2. for i in range(0,np.size(bins)-1)])
        hist = np.histogram(np.log10(diff),bins,density=True)[0]
        plt.plot(mbin,hist,color=color,label=self.label,ls=ls)

    def plot_Z_vs_vel_width(self,elem="Si", ion=2, color="blue",color2="darkblue"):
        """Plot the correlation between metallicity and velocity width"""
        vel = self.vel_width(elem, ion)
        met = self.get_metallicity()
        #Ignore objects too faint to be seen
        ind2 = np.where(met > 1e-4)
        met = met[ind2]
        vel = vel[ind2]
        self._plot_2d_contour(vel, met, 10, "Z vel sim", color, color2, fit=True)
        plt.xlim(10,2e3)
        plt.ylabel(r"$\mathrm{Z} / \mathrm{Z}_\odot$")
        plt.xlabel(r"$v_\mathrm{90}$ (km s$^{-1}$)")

    def plot_Z_vs_mass(self,color="blue", color2="darkblue"):
        """Plot the correlation between mass and metallicity, with a fit"""
        (halo, _) = self.find_nearest_halo()
        ind = np.where(halo > 0)
        met = self.get_metallicity()[ind]
        mind = np.where(met > 1e-4)
        halo = halo[ind]
        mass = self.sub_mass[halo]
        mass = mass[mind]
        met = met[mind]
        self._plot_2d_contour(mass+0.1, met, 10, "Z mass", color, color2)
        plt.ylim(1e-4,1)

    def plot_vel_vs_mass(self,elem, ion, color="blue",color2="darkblue"):
        """Plot the correlation between mass and metallicity, with a fit"""
        vel = self.vel_width(elem, ion)
        self._plot_xx_vs_mass(vel, "vel",color,color2)

    def _plot_xx_vs_mass(self, xx, name = "xx", color="blue", color2="darkblue", log=True):
        """Helper function to plot something against virial velocity"""
        (halo, _) = self.find_nearest_halo()
        ii = self.get_filt("Si",2)
        ind = np.where(halo[ii] > 0)
        halo = halo[ii][ind]
        xx = xx[ii][ind]
        virial = self.virial_vel(halo)+0.1
        self._plot_2d_contour(virial, xx, 10, name+" virial velocity", color, color2, ylog=log)

    def _plot_2d_contour(self, xvals, yvals, nbins, name="x y", color="blue", color2="darkblue", ylog=True, xlog=True, fit=False, sample=40.):
        """Helper function to make a 2D contour map of a correlation, as well as the best-fit linear fit"""
        if ylog:
            yvals = np.log10(yvals)
        if xlog:
            xvals = np.log10(xvals)
        (H, xedges, yedges) = np.histogram2d(xvals, yvals,bins=nbins)
        xbins=np.array([(xedges[i+1]+xedges[i])/2 for i in xrange(0,np.size(xedges)-1)])
        ybins=np.array([(yedges[i+1]+yedges[i])/2 for i in xrange(0,np.size(yedges)-1)])
        xx = np.logspace(np.min(xbins), np.max(xbins),15)
        ax = plt.gca()
        if ylog:
            ybins = 10**ybins
            ax.set_yscale('log')
        if xlog:
            xbins = 10**xbins
            ax.set_xscale('log')
        plt.contourf(xbins,ybins,H.T,(self.NumLos/sample)*np.array([0.15,1,10]),colors=(color,color2,"black"),alpha=0.5)
        if fit:
            (intercept, slope, _) = lsq.leastsq(xvals,yvals)
            plt.loglog(xx, 10**intercept*xx**slope, color="black",label=self.label, ls="--")

    def kstest(self, Zdata, veldata, elem="Si", ion=2):
        """Find the 2D KS test value of the vel width and log metallicity
           with respect to an external dataset, veldata and Z data"""
        met = self.get_metallicity()
        ind = self.get_filt(elem, ion)
        met = np.log10(met[ind])
        vel = np.log10(self.vel_width(elem, ion)[ind])
        data2 = np.array([met,vel]).T
        data = np.array([np.log10(Zdata), np.log10(veldata)]).T
        return ks.ks_2d_2samp(data,data2)

    def plot_virial_vel_vs_vel_width(self,elem, ion,color="red", ls="-", label="", dm=0.1):
        """Plot a histogram of the velocity widths vs the halo virial velocity"""
        (halos, _) = self.find_nearest_halo()
        ind = self.get_filt(elem,ion)
        f_ind = np.where(halos[ind] != -1)
        vel = self.vel_width(elem, ion)[ind][f_ind]
        virial = self.virial_vel(halos[ind][f_ind])+0.1
        vvvir = vel/virial
        m_table = 10**np.arange(np.log10(np.min(vvvir)), np.log10(np.max(vvvir)), dm)
        mbin = np.array([(m_table[i]+m_table[i+1])/2. for i in range(0,np.size(m_table)-1)])
        pdf = np.histogram(np.log10(vvvir),np.log10(m_table), density=True)[0]
        print "median v/vir: ",np.median(vvvir)
        plt.semilogx(mbin, pdf, color=color, ls=ls, label=label)
        return (mbin, pdf)

class PlotHaloSpectra(halospectra.HaloSpectra, PlottingSpectra):
    """Class to plot things connected with spectra."""
    def __init__(self,num, base, repeat = 3, minpart = 400, res = 1., savefile="halo_spectra_DLA.hdf5"):
        halospectra.HaloSpectra.__init__(self,num, base, repeat, minpart, res, savefile)
try:
    import convert_cloudy

    class PlotIonDensity:
        """Class to plot the ionisation fraction of elements as a function of density"""
        def __init__(self, red):
            self.cloudy_table = convert_cloudy.CloudyTable(red)
            self.red = red

        def iondensity(self,elem,ion, metal = 0.1, den=(-2.,3)):
            """Plot the ionisation fraction of an ionic species as a function of hydrogen density.
            Arguments:
                elem, ion - specify the species to plot
                metal - metallicity as a fraction of solar for this species
                den - range of densities to plot
            """
            #Bins in density
            dens = 10**np.arange(den[0],den[1],0.2)
            mass_frac = self.cloudy_table.get_solar(elem)*metal*np.ones(np.size(dens))
            ionfrac = self.cloudy_table.ion(elem, ion, mass_frac, dens)
            plt.loglog(dens,ionfrac)
except ImportError:
    pass
