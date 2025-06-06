within Greenhouses.Interfaces.Heat;
model ThermalPortConverter
  "Convert duplicated single thermal ports into one single multi-port"
  parameter Integer N = 10;
  ThermalPort                                     multi(final N=N)
    annotation (Placement(transformation(extent={{-36,28},{36,42}})));
  ThermalPortL                                     single[N]
     annotation (Placement(transformation(extent={{-36,-48},{36,-34}})));
equation
  for i in 1:N loop
    single[i].T = multi.T[i];
    single[i].phi = -multi.phi[i];
  end for;
  annotation (Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-100,
            -100},{100,100}}), graphics),
    Icon(coordinateSystem(preserveAspectRatio=false, extent={{-100,-100},{100,100}}),
        graphics={Text(
          extent={{-34,-20},{34,-34}},
          lineColor={0,0,255},
          textString="Single"), Text(
          extent={{-34,26},{34,12}},
          lineColor={0,0,255},
          textString="Multi")}));
end ThermalPortConverter;
