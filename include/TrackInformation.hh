#ifndef TrackInformation_h
#define TrackInformation_h 1

#include "G4VUserTrackInformation.hh"
#include "globals.hh"

class TrackInformation : public G4VUserTrackInformation
{
  public:
    TrackInformation()
    : G4VUserTrackInformation(),
      fHadLeadInteraction(false),
      fHadHolderInteraction(false)
    {}

    TrackInformation(G4bool hadLeadInteraction, G4bool hadHolderInteraction)
    : G4VUserTrackInformation(),
      fHadLeadInteraction(hadLeadInteraction),
      fHadHolderInteraction(hadHolderInteraction)
    {}

    virtual ~TrackInformation() {}

    void SetLeadInteraction(G4bool value)
    {
        fHadLeadInteraction = value;
    }

    void SetHolderInteraction(G4bool value)
    {
        fHadHolderInteraction = value;
    }

    G4bool HasLeadInteraction() const
    {
        return fHadLeadInteraction;
    }

    G4bool HasHolderInteraction() const
    {
        return fHadHolderInteraction;
    }

  private:
    G4bool fHadLeadInteraction;
    G4bool fHadHolderInteraction;
};

#endif
