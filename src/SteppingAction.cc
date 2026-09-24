#include "SteppingAction.hh"
#include "TrackInformation.hh"

#include "G4Step.hh"
#include "G4Track.hh"
#include "G4StepPoint.hh"
#include "G4VPhysicalVolume.hh"
#include "G4VProcess.hh"
#include "G4String.hh"

#include <string>

SteppingAction::SteppingAction()
: G4UserSteppingAction()
{}

SteppingAction::~SteppingAction()
{}

void SteppingAction::UserSteppingAction(const G4Step* step)
{
    G4Track* track = step->GetTrack();

    TrackInformation* info =
        dynamic_cast<TrackInformation*>(track->GetUserInformation());

    if (!info) {
        info = new TrackInformation(false, false);
        track->SetUserInformation(info);
    }

    G4bool leadTagged = info->HasLeadInteraction();
    G4bool holderTagged = info->HasHolderInteraction();

    G4StepPoint* prePoint = step->GetPreStepPoint();
    G4StepPoint* postPoint = step->GetPostStepPoint();

    G4VPhysicalVolume* preVolume = prePoint->GetPhysicalVolume();
    const G4VProcess* process = postPoint->GetProcessDefinedStep();

    G4bool inLeadVolume = false;
    G4bool inHolderVolume = false;

    if (preVolume) {
        G4String volName = preVolume->GetName();

        if (volName.find("Lead") != std::string::npos) {
            inLeadVolume = true;
        }

        // This tags interactions in the holder material, not in the TLD itself.
        // The physical holder volume is named "Holder" in DetectorConstruction.cc.
        if (volName == "Holder") {
            inHolderVolume = true;
        }
    }

    if (process) {
        G4String procName = process->GetProcessName();

        if (procName != "Transportation") {
            if (inLeadVolume) {
                info->SetLeadInteraction(true);
                leadTagged = true;
            }

            if (inHolderVolume) {
                info->SetHolderInteraction(true);
                holderTagged = true;
            }
        }
    }

    const auto* secondaries = step->GetSecondaryInCurrentStep();

    if (secondaries) {
        for (auto secondaryTrackConst : *secondaries) {
            G4Track* secondaryTrack =
                const_cast<G4Track*>(secondaryTrackConst);

            TrackInformation* secondaryInfo =
                dynamic_cast<TrackInformation*>(secondaryTrack->GetUserInformation());

            if (!secondaryInfo) {
                secondaryInfo = new TrackInformation(leadTagged, holderTagged);
                secondaryTrack->SetUserInformation(secondaryInfo);
            } else {
                secondaryInfo->SetLeadInteraction(leadTagged);
                secondaryInfo->SetHolderInteraction(holderTagged);
            }
        }
    }
}
