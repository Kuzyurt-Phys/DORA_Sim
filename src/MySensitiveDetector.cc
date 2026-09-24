#include "MySensitiveDetector.hh"
#include "TrackInformation.hh"

#include "G4Step.hh"
#include "G4Track.hh"
#include "G4ParticleDefinition.hh"
#include "G4AnalysisManager.hh"
#include "G4SystemOfUnits.hh"

MySensitiveDetector::MySensitiveDetector(G4String name)
: G4VSensitiveDetector(name)
{}

MySensitiveDetector::~MySensitiveDetector()
{}

G4bool MySensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory*)
{
    G4double edep = step->GetTotalEnergyDeposit();

    if (edep <= 0.0) {
        return false;
    }

    G4int copyNo =
        step->GetPreStepPoint()->GetTouchable()->GetCopyNumber();

    G4Track* track = step->GetTrack();

    TrackInformation* info =
        dynamic_cast<TrackInformation*>(track->GetUserInformation());

    G4int fromLeadInteraction = 0;
    G4int fromHolderInteraction = 0;

    if (info) {
        if (info->HasLeadInteraction()) {
            fromLeadInteraction = 1;
        }

        if (info->HasHolderInteraction()) {
            fromHolderInteraction = 1;
        }
    }

    G4int pdg = 0;

    if (track->GetDefinition()) {
        pdg = track->GetDefinition()->GetPDGEncoding();
    }

    G4int parentID = track->GetParentID();

    auto analysisManager = G4AnalysisManager::Instance();

    analysisManager->FillNtupleIColumn(0, copyNo);
    analysisManager->FillNtupleDColumn(1, edep / keV);
    analysisManager->FillNtupleIColumn(2, fromLeadInteraction);
    analysisManager->FillNtupleIColumn(3, fromHolderInteraction);
    analysisManager->FillNtupleIColumn(4, pdg);
    analysisManager->FillNtupleIColumn(5, parentID);

    analysisManager->AddNtupleRow();

    return true;
}
