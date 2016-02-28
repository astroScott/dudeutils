#include<stdio.h>
#include<math.h>
#include"spectrum.h"


  
double voigt(double v, double a){

    const double h0[] = {
        1.0000000, 0.9900500, 0.9607890, 0.9139310, 0.8521440, 0.7788010,
        0.6976760, 0.6126260, 0.5272920, 0.4448580, 0.3678790, 0.2984970,
        0.2369280, 0.1845200, 0.1408580, 0.1053990, 0.0773050, 0.0555760,
        0.0391640, 0.0270520, 0.0183156, 0.0121552, 0.0079071, 0.0050418,
        0.0031511, 0.0019305, 0.0011592, 0.0006823, 0.0003937, 0.0002226,
        0.0001234, 0.0000671, 0.0000357, 0.0000186, 0.0000095, 0.0000048,
        0.0000024, 0.0000011, 0.0000005, 0.0000002, 0.0000001 };


    const double h1[] = { 
        -1.1283800,-1.1059600,-1.0404800,-0.9370300,-0.8034600,-0.6494500,
        -0.4855200,-0.3219200,-0.1677200,-0.0301200, 0.0859400, 0.1778900,
        0.2453700, 0.2898100, 0.3139400, 0.3213000, 0.3157300, 0.3009400,
        0.2802700, 0.2564800, 0.2317260, 0.2075280, 0.1848820, 0.1643410,
        0.1461280, 0.1302360, 0.1165150, 0.1047390, 0.0946530, 0.0860050,
        0.0785650, 0.0721290, 0.0665260, 0.0616150, 0.0572810, 0.0534300,
        0.0499880, 0.0468940, 0.0440980, 0.0415610, 0.0392500, 0.0351950,
        0.0317620, 0.0288240, 0.0262880, 0.0240810, 0.0221460, 0.0204410,
        0.0189290, 0.0175820, 0.0163750, 0.0152910, 0.0143120, 0.0134260,
        0.0126200, 0.0118860, 0.0112145, 0.0105990, 0.0100332, 0.0095119,
        0.0090306, 0.0085852, 0.0081722, 0.0077885, 0.0074314, 0.0070985,
        0.0067875, 0.0064967, 0.0062243, 0.0059688, 0.0057287, 0.0055030,
        0.0052903, 0.0050898, 0.0049006, 0.0047217, 0.0045526, 0.0043924,
        0.0042405, 0.0040964, 0.0039595 };


    const double h2[] = {
        1.0000000, 0.9702000, 0.8839000, 0.7494000, 0.5795000, 0.3894000,
        0.1953000, 0.0123000,-0.1476000,-0.2758000,-0.3679000,-0.4234000,
        -0.4454000,-0.4392000,-0.4113000,-0.3689000,-0.3185000,-0.2657000,
        -0.2146000,-0.1683000,-0.1282100,-0.0950500,-0.0686300,-0.0483000,
        -0.0331500,-0.0222000,-0.0145100,-0.0092700,-0.0057800,-0.0035200,
        -0.0021000,-0.0012200,-0.0007000,-0.0003900,-0.0002100,-0.0001100,
        -0.0000600,-0.0000300,-0.0000100,-0.0000100, 0.0000000 };

    double v0, v1, v2;
    int   n, n1;
    //int v0;
    
    if(v < 0.0)  v = -v;

    v0 = v*10.0;
    n = v0;
    if (n < 40.) {
      v1 = (double)n;
      v2 = v0-v1;
      n1 = n+1;
      return v2*(h0[n1]-h0[n]+a*(h1[n1]-h1[n]+a*(h2[n1]-h2[n]))) +
        h0[n]+a*(h1[n]+a*h2[n]);
    }
    else if (n < 120.) {
      n = n/2 + 20;
      v1 = ((double)n-20.)*2.;
      v2 = (v0-v1)/2.0;
      n1 = n+1;
      return a*((h1[n1]-h1[n])*v2+h1[n]);
    }
    else {
      return (0.56419 + 0.846/(v*v))/(v*v)*a;
    }
  }
  
  
