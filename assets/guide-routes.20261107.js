/* Booking guidance for selected visit goals. Safety and the visitor's choices stay in the guide. */
(() => {
  'use strict';

  const goals = [
    {id: 'investigate', label: 'Få besväret undersökt', description: 'Jag vill förstå vad som kan ligga bakom.'},
    {id: 'rehab', label: 'Få hjälp med behandling och rehab', description: 'Jag vill veta vad jag kan göra för att komma vidare.'},
    {id: 'injection', label: 'Förstå mina alternativ för injektion', description: 'Jag vill läsa om alternativ och vad som bedöms före behandling.'},
    {id: 'unsure', label: 'Jag är osäker', description: 'Jag vill börja med en undersökning och få hjälp att välja nästa steg.'}
  ];

  const kneeJoint = {title: 'Svullnad och artrosförändringar i knät', href: '/ultraljud/kna/#artros'};
  const achillesCase = {title: 'Stel och öm hälsena vid belastning', href: '/ultraljud/halsena/bilder/'};
  const lateralHipCase = {title: 'Ont på utsidan av höften', href: '/ultraljud/glutealsenor/bilder/'};
  const hipJointCase = {title: 'Så undersöktes höftleden före en injektion', href: '/ultraljud/hoftled/bilder/'};
  const shoulderCase = {title: 'Ont när du lyfter armen', href: '/ultraljud/kalkaxel/'};

  const areas = {
    shoulder: {
      exam: 'Vi undersöker hur axeln rör sig, vad som påverkar styrkan och vilka rörelser som väcker besvären.',
      ultrasound: {href: '/ultraljud/axel/', reason: 'Vid en riktad fråga om axelns senor eller slemsäckar kombinerar vi ultraljud med en undersökning av axeln.'},
      imagingPatterns: ['lifting', 'night', 'rehab'],
      cases: {
        lifting: shoulderCase,
        night: {title: 'Värk i axeln och fynd kring slemsäck och senor', href: '/ultraljud/bursit-axel/'},
        rehab: shoulderCase
      },
      joint: {label: 'axeln', href: '/hyaluronsyra/axel/#boka-hyaluron'}
    },
    knee: {
      exam: 'Vi undersöker knäets rörlighet, styrka, belastning och eventuell svullnad. Sedan går vi igenom vad som kan vara ett rimligt nästa steg.',
      ultrasound: {href: '/ultraljud/kna/', reason: 'Vid en riktad fråga kan ultraljud komplettera undersökningen av knäets vätska, senor och andra ytliga strukturer.'},
      imagingPatterns: ['running', 'swelling'],
      cases: {
        running: {title: 'Smärta på knäts utsida vid löpning', href: '/ultraljud/loparkna/'},
        swelling: kneeJoint,
        arthritis: kneeJoint
      },
      joint: {
        label: 'knät', href: '/hyaluronsyra/kna/#boka',
        patientCase: {title: 'Knäartros och individuell bedömning inför hyaluron', href: '/ultraljud/kna/artros-ledband-hyaluron/'},
        related: {title: 'Läs om PRP och hyaluron vid knäartros', href: '/blogg/prp-eller-hyaluronsyra-vid-knaartros/'}
      }
    },
    hip: {
      exam: 'Vi undersöker höftens rörlighet och styrka, hur besvären påverkar gång och belastning och om något närliggande område behöver undersökas.',
      ultrasound: {href: '/ultraljud/hoft-ljumske/', reason: 'Vid en riktad fråga om senor eller andra mjukdelar runt höften kan ultraljud komplettera undersökningen.'},
      imagingPatterns: ['side'],
      cases: {side: lateralHipCase},
      joint: {label: 'höften', href: '/hyaluronsyra/hoft/#boka-hyaluron', patientCase: hipJointCase}
    },
    lowerLeg: {
      exam: 'Vi undersöker var besvären sitter i underbenet och hur gång, rörelse och belastning påverkar dem.',
      ultrasound: {href: '/ultraljud/underben/', reason: 'Vid en riktad fråga om vadens muskler eller senor kan ultraljud komplettera undersökningen.'},
      imagingPatterns: ['calf'],
      related: {title: 'Läs om ultraljud av vad och underben', href: '/ultraljud/underben/'}
    },
    achilles: {
      exam: 'Vi undersöker hälsenan, fotledens rörlighet och hur besvären påverkar gång och belastning.',
      ultrasound: {href: '/ultraljud/halsena/', reason: 'Vid en riktad fråga om hälsenan kan ultraljud komplettera undersökningen. Bilderna bedöms tillsammans med hur senan fungerar vid belastning.'},
      imagingPatterns: ['tendon', 'achilles', 'load'],
      cases: {tendon: achillesCase, achilles: achillesCase, load: achillesCase}
    },
    foot: {
      exam: 'Vi undersöker fotens och fotledens rörlighet och hur gång, styrka och belastning påverkar besvären.'
    },
    elbow: {
      exam: 'Vi undersöker armbågens rörlighet, grepp och styrka och hur belastning påverkar besvären.',
      cases: {outside: {title: 'Ont på armbågens utsida vid grepp och lyft', href: '/ultraljud/tennisarmbage/bilder/'}}
    },
    hand: {
      exam: 'Vi undersöker rörelse, grepp och belastning. Vid domningar kan vi även behöva undersöka känsel och nervfunktion.',
      cases: {night: {title: 'Domningar i handen och ultraljud av nerven', href: '/ultraljud/hand-handled/karpaltunnelsyndrom/'}}
    },
    back: {
      exam: 'Vi går igenom var besvären sitter, hur rörelser påverkar dem och om känsel eller styrka har förändrats.'
    }
  };

  function clinicalRoute(reason) {
    return {
      id: 'naprapati',
      title: 'Naprapatisk bedömning',
      reason,
      href: '/naprapati/',
      label: 'Läs om naprapatisk bedömning',
      bookingKey: 'naprapati'
    };
  }

  function imagingRoute({href, reason}) {
    return {
      id: 'ultraljud',
      title: 'Muskuloskeletalt ultraljud',
      reason,
      href,
      label: 'Läs om ultraljud',
      bookingKey: 'ultraljud'
    };
  }

  function resolve({area, pattern, goal, assessedJoint}) {
    const isAchilles = (area === 'foot' || area === 'lowerLeg') && pattern === 'achilles';
    const region = areas[isAchilles ? 'achilles' : area];
    const caseForPattern = region?.cases?.[pattern];
    const clinical = clinicalRoute(region?.exam || 'Vi undersöker besväret och går igenom ett rimligt nästa steg.');
    const imaging = region?.imagingPatterns?.includes(pattern) ? imagingRoute(region.ultrasound) : null;
    const joint = region?.joint;
    const hasAssessment = assessedJoint === true || (assessedJoint === undefined && area === 'knee' && pattern === 'arthritis');

    if (goal === 'injection' && joint && hasAssessment) {
      return {
        primary: {
          id: 'hyaluron',
          title: 'Hyaluron i ' + joint.label,
          reason: 'Du har redan fått leden bedömd och vill läsa om injektion. På tjänstesidan kan du läsa om forskningsläget, besöket och vad som vägs in innan behandling kan bli aktuell.',
          href: joint.href,
          label: 'Se pris och bokning för hyaluron'
        },
        alternative: clinical,
        patientCase: joint.patientCase || null,
        related: joint.related || {title: 'Läs om andra injektionsalternativ', href: '/injektioner/#in-1'},
        nextSteps: 'Ta gärna med tidigare utlåtanden. Vid besöket går vi igenom din tidigare bedömning, vad du har provat och vilka alternativ som kan vara aktuella.'
      };
    }

    if (goal === 'investigate' && imaging) {
      return {
        primary: imaging,
        alternative: clinical,
        patientCase: caseForPattern || null,
        related: region.related || null,
        nextSteps: 'Vid besöket går vi igenom din fråga och förklarar vad undersökningen visar. Därefter diskuterar vi om du behöver rehab, uppföljning eller annan bedömning.'
      };
    }

    return {
      primary: clinical,
      alternative: goal === 'injection' ? null : imaging,
      patientCase: caseForPattern || null,
      related: null,
      nextSteps: goal === 'injection'
        ? 'Börja med att få besväret bedömt. Efter undersökningen kan du och din behandlare gå igenom vilka alternativ som är relevanta.'
        : 'Efter undersökningen pratar vi om nästa steg utifrån vad du vill kunna göra. Det kan vara en plan för rehab, uppföljning eller kompletterande undersökning.'
    };
  }

  window.KanseiGuideRoutes = {goals, resolve};
})();
