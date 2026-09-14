// BIEM BM-ICC-08 original RFQ/EVT Rev A. Not released manufacturing CAD.
// Connector positions and actuator are sample-dependent. Dimensions in mm.
W=360; D=260; H=86; t=2; panel=3; rack=true; lid=true; internals=true;
$fn=48;
module rear(){
 difference(){
  translate([0,D-panel,0]) cube([W,panel,H]);
  for(x=[250,320]){
   translate([x,D+1,43])rotate([90,0,0])cylinder(h=panel+2,r=29);
   for(dx=[-25,25],dz=[-25,25])translate([x+dx,D+1,43+dz])rotate([90,0,0])cylinder(h=panel+2,r=2.15);
  }
 }
}
module chassis(){
 color([.18,.20,.23]){
  translate([0,panel,0])cube([W,D-2*panel,t]);
  translate([0,panel,t])cube([t,D-2*panel,H-2*t]);
  translate([W-t,panel,t])cube([t,D-2*panel,H-2*t]);
  if(lid)translate([0,panel,H-t])cube([W,D-2*panel,t]);
  rear();
 }
 color([.77,.79,.80])cube([W,panel,H]);
 color([.50,.09,.19])translate([17,-.3,8])cube([4,.3,70]);
}
module ear(right=false){
 sx=right ? W : -61.3;
 color([.15,.17,.20]){
  translate([sx,0,0])cube([61.3,3,H]);
  translate([right ? W : -3,0,0])cube([3,60,H]);
 }
}
chassis();
if(rack){ear(false);ear(true);}
if(internals){
 color([.55,.56,.57])translate([30,26,7])cube([300,200,2]);
 color([.25,.30,.35])translate([208,45,12])cube([117,112,49.2]);
 for(y=[83,140])color([.45,.48,.51])translate([43,y,12])cube([105,35,22]);
 color([.52,.56,.58])translate([178,40,2])cube([1,185,55]);
 for(x=[250,320])color([.34,.28,.20])translate([x-30,231,13])cube([60,25,60]);
}
// Ghost markers: HOLD positions; do not infer finished cutouts.
for(x=[35,70,155,200,112])color([.95,.55,.15,.6])translate([x,D,43])rotate([90,0,0])cylinder(h=2,r=x<100?5:12);
