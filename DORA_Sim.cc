// ----------------------------------------------------------------------------
// DORA_Sim.cc
// Main entry point for the DORA Irradiator Simulation.
// ----------------------------------------------------------------------------

#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"

#include "DetectorConstruction.hh"
#include "ActionInitialization.hh"
#include "FTFP_BERT.hh"
#include "G4EmStandardPhysics_option4.hh"

int main(int argc,char** argv)
{
  // Detect interactive mode (if no arguments) and define UI session
  G4UIExecutive* ui = nullptr;
  if ( argc == 1 ) {
    ui = new G4UIExecutive(argc, argv);
  }

  // Construct the run manager
  auto* runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Default);

  // Set mandatory initialization classes
  runManager->SetUserInitialization(new DetectorConstruction());

  // Use High-Precision EM Physics (Option 4) for accurate dose calculation
  G4VModularPhysicsList* physicsList = new FTFP_BERT;
  physicsList->ReplacePhysics(new G4EmStandardPhysics_option4());
  runManager->SetUserInitialization(physicsList);

  // Set user action classes
  runManager->SetUserInitialization(new ActionInitialization());

  // Initialize visualization
  G4VisManager* visManager = new G4VisExecutive;
  visManager->Initialize();

  // Get the pointer to the User Interface manager
  G4UImanager* UImanager = G4UImanager::GetUIpointer();

  // Process macro or start UI session
  if ( ! ui ) {
    // batch mode
    G4String command = "/control/execute ";
    G4String fileName = argv[1];
    UImanager->ApplyCommand(command+fileName);
  }
  else {
    // interactive mode
    UImanager->ApplyCommand("/control/execute init_vis.mac");
    ui->SessionStart();
    delete ui;
  }

  delete visManager;
  delete runManager;
}
