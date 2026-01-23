from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
import pandas as pd
from .forms import UploadExcelForm, CustomUserCreationForm, PersonForm
from .models import Person, UploadLog
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView
from .forms import PersonManualForm
from django.db.models.functions import Cast, Trim
from django.db.models import Func
from django.db.models import IntegerField, Value, CharField, F, Q, Max
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django import forms





def incomplete_records(request):
    # Get records where ALL fields (except ari8mosEisagoghs and hmeromhnia_eis) are null
    incomplete = Person.objects.filter(
        Q(syggrafeas__isnull=True) &
        Q(koha__isnull=True) &
        Q(titlos__isnull=True) &
        Q(ekdoths__isnull=True) &
        Q(ekdosh__isnull=True) &
        Q(etosEkdoshs__isnull=True) &
        Q(toposEkdoshs__isnull=True) &
        Q(sxhma__isnull=True) &
        Q(selides__isnull=True) &
        Q(tomos__isnull=True) &
        #Q(troposPromPar__isnull=True) &
        Q(ISBN__isnull=True) &
        Q(sthlh1__isnull=True) &
        Q(sthlh2__isnull=True)
    ).order_by('ari8mosEisagoghs')  # Order to get first one consistently
    
    count = incomplete.count()
    first_incomplete = incomplete.first()  # Get the first incomplete record
    
    return render(request, 'incomplete_records.html', {
        'count': count,
        'records': incomplete[:100],  # Show first 100 records
        'total_records': Person.objects.count(),
        'first_incomplete': first_incomplete,  # Pass to template
    })




@login_required
def autocomplete_title(request):
    q = request.GET.get('q', '')
    results = (
        Person.objects.filter(titlos__icontains=q)
        .values_list('titlos', flat=True)
        .distinct()[:10]
    )
    return JsonResponse({'results': list(results)})


@login_required
def autocomplete_ekdoths(request):
    q = request.GET.get('q', '')
    results = (
        Person.objects.filter(ekdoths__icontains=q)
        .values_list('ekdoths', flat=True)
        .distinct()[:10]
    )
    return JsonResponse({'results': list(results)})

def home(request):
    return render(request, 'home.html')

class SignUpView( CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
    
    
    

def clean(value):
    if pd.isna(value):
        return None
    return str(value).strip()
    
def clean_ari8mos(value):
    if pd.isna(value):
        return None
    try:
        return str(int(value))  # 115011.0 → "115011"
    except (ValueError, TypeError):
        return str(value).strip() 

def clean_numeric_or_text(value):
    """
    For fields that can be numeric (like year "2012") or contain 
    special characters (like "[2012]"). Removes .0 from clean numbers
    but preserves text with special characters.
    """
    if pd.isna(value):
        return None
    
    # If it's a float and a whole number, convert to int then string
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))  # 2012.0 → "2012"
        return str(value).strip()  # 2012.5 → "2012.5"
    
    # Otherwise just convert to string
    return str(value).strip()

@login_required
def show_people(request):
    qs = (
        Person.objects
        .exclude(ari8mosEisagoghs__isnull=True)
        .order_by("ari8mosEisagoghs")
    )

    # 🔍 Search
    search = request.GET.get('search', '').strip()
    search_category = request.GET.get('search_category', 'all')  # New parameter
    
    if search:
        if search_category == 'all':
            # Search all fields (original behavior)
            q = Q(titlos__icontains=search) | Q(syggrafeas__icontains=search)
            
            if search.isdigit():
                q |= Q(ari8mosEisagoghs=int(search))
                
            qs = qs.filter(q)
            
        elif search_category == 'ari8mos':
            # Search only by number
            if search.isdigit():
                qs = qs.filter(ari8mosEisagoghs=int(search))
            else:
                # If non-numeric input for number search, show no results
                qs = qs.none()
                
        elif search_category == 'hmeromhnia_eis':
            # Search only by hmeromhnia_eis
            qs = qs.filter(hmeromhnia_eis__icontains=search)
            
        elif search_category == 'titlos':
            # Search only by title
            qs = qs.filter(titlos__icontains=search)
            
        elif search_category == 'syggrafeas':
            # Search only by author
            qs = qs.filter(syggrafeas__icontains=search)
            
        elif search_category == 'ekdoths':
            # Search only by publisher
            qs = qs.filter(ekdoths__icontains=search)
            
        elif search_category == 'ISBN':
            # Search only by ISBN
            qs = qs.filter(ISBN__icontains=search)
            
        
    # 📊 Range filter
    from_num = request.GET.get('from_num')
    to_num = request.GET.get('to_num')
    
    if from_num and to_num:
       qs = qs.filter(
          ari8mosEisagoghs__gte=int(from_num),
          ari8mosEisagoghs__lte=int(to_num)
       )
       
    # 📄 Pagination
    paginator = Paginator(qs, 200)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)  

    # ✅ AJAX request - return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('main/people_table_rows.html', {
            'page_obj': page_obj
        },
            request=request 
        )
        return JsonResponse({
            'html': html,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'current_page': page_obj.number,
            'total_pages': page_obj.paginator.num_pages,
        })
        


    return render(request, "main/people.html", {
        "page_obj": page_obj,
        "search": search,
        "search_category": search_category,
        
        
    })




def generate_koha_from_author(author):
    """
    Converts 'surname,name,extra' → 'name surname extra'
    """
    if not author or "," not in author:
        return None
    
    
    # Normalize commas
    author = author.replace("，", ",")

    parts = [p.strip() for p in author.split(",") if p.strip()]
    
    if len(parts) < 2:
        return None

    surname = parts[0]
    name = parts[1]
    extra = " ".join(parts[2:]) if len(parts) > 2 else ""
    result = f"{name} {surname}"
    if extra:
        result = f"{result} {extra}"
        
    return result


@login_required
def upload_excel(request):
    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file)
            
            # ✅ υπάρχοντα IDs στη βάση
            existing_ids = set(
                Person.objects.values_list('ari8mosEisagoghs', flat=True)
            )

            # 🔴 Νέο set για να εντοπίζει διπλότυπα μέσα στο ίδιο Excel
            seen_in_file = set()

            added = []
            skipped = []
            duplicates = []
            potential_insertions = []  # NEW: για κενές εγγραφές
            new_objects = []

            for index, row in df.iterrows():
                raw_ari8mos = clean_ari8mos(row.get('ΑΡΙΘΜΟΣ ΕΙΣΑΓΩΓΗΣ'))
                syggrafeas = clean(row.get('ΣΥΓΓΡΑΦΕΑΣ'))
                koha = clean(row.get('ΣΥΓΓΡΑΦΕΑΣ KOHA'))
                
                if (koha is None or koha == "") and syggrafeas:
                   koha = generate_koha_from_author(syggrafeas)
                
                try:
                    ari8mos = int(raw_ari8mos)
                except (TypeError, ValueError):
                    skipped.append({
                      'row': index + 2,
                      'reason': 'Invalid ΑΡΙΘΜΟΣ ΕΙΣΑΓΩΓΗΣ'
                    })
                    continue

                if not ari8mos:
                    skipped.append({
                        'row': index + 2,
                        'reason': 'Missing ΑΡΙΘΜΟΣ ΕΙΣΑΓΩΓΗΣ'
                    })
                    continue

                # 🔴 DUPLICATE ΜΕΣΑ ΣΤΟ ΙΔΙΟ EXCEL
                if ari8mos in seen_in_file:
                    skipped.append({
                        'row': index + 2,
                        'reason': 'Duplicate ΑΡΙΘΜΟΣ ΕΙΣΑΓΩΓΗΣ inside Excel'
                    })
                    continue
                seen_in_file.add(ari8mos)

                # 🔴 DUPLICATE CHECK (existing_ids = βάση δεδομένων)
                if ari8mos in existing_ids:
                    existing_person = Person.objects.filter(ari8mosEisagoghs=ari8mos).first()

                    if not existing_person:
                        # Ασφαλές insert
                        new_objects.append(Person(
                            ari8mosEisagoghs=ari8mos,
                            hmeromhnia_eis=clean_numeric_or_text(row.get('ΗΜΕΡΟΜΗΝΙΑ ΕΙΣΑΓΩΓΗΣ')),
                            syggrafeas=clean(row.get('ΣΥΓΓΡΑΦΕΑΣ')),
                            koha=koha,
                            titlos=clean(row.get('ΤΙΤΛΟΣ')),
                            ekdoths=clean(row.get('ΕΚΔΟΤΗΣ')),
                            ekdosh=clean(row.get('ΕΚΔΟΣΗ')),
                            etosEkdoshs=clean_numeric_or_text(row.get('ΕΤΟΣ ΕΚΔΟΣΗΣ')),
                            toposEkdoshs=clean(row.get('ΤΟΠΟΣ  ΕΚΔΟΣΗΣ')),
                            sxhma=clean(row.get('ΣΧΗΜΑ')),
                            selides=clean(row.get('ΣΕΛΙΔΕΣ')),
                            tomos=clean(row.get('ΤΟΜΟΣ')),
                            troposPromPar=clean(row.get('ΤΡΟΠΟΣ ΠΡΟΜΗΘΕΙΑΣ ΠΑΡΑΤΗΡΗΣΕΙΣ')),
                            ISBN=clean_numeric_or_text(row.get('ISBN')),
                            sthlh1=clean_numeric_or_text(row.get('Στήλη1')),
                            sthlh2=clean_numeric_or_text(row.get('Στήλη2')),
                        ))
                        existing_ids.add(ari8mos)
                        continue

                    # ✅ NEW: Check if existing record is empty (all fields null except ari8mos and hmeromhnia_eis)
                    is_empty_record = all([
                        not existing_person.syggrafeas,
                        not existing_person.koha,
                        not existing_person.titlos,
                        not existing_person.ekdoths,
                        not existing_person.ekdosh,
                        not existing_person.etosEkdoshs,
                        not existing_person.toposEkdoshs,
                        not existing_person.sxhma,
                        not existing_person.selides,
                        not existing_person.tomos,
                        #not existing_person.troposPromPar,
                        not existing_person.ISBN,
                        not existing_person.sthlh1,
                        not existing_person.sthlh2,
                    ])

                    if is_empty_record:
                        # This is a potential new insertion (empty record in DB)
                        potential_insertions.append({
                            "ari8mos": ari8mos,
                            "database": {
                                "ari8mos": existing_person.ari8mosEisagoghs,
                                "hmeromhnia_eis": existing_person.hmeromhnia_eis,
                            },
                            "excel": {
                                "ari8mos": ari8mos,
                                "hmeromhnia_eis": clean_numeric_or_text(row.get('ΗΜΕΡΟΜΗΝΙΑ ΕΙΣΑΓΩΓΗΣ')),
                                "syggrafeas": clean(row.get('ΣΥΓΓΡΑΦΕΑΣ')),
                                "koha": koha,
                                "titlos": clean(row.get('ΤΙΤΛΟΣ')),
                                "ekdoths": clean(row.get('ΕΚΔΟΤΗΣ')),
                                "ekdosh": clean(row.get('ΕΚΔΟΣΗ')),
                                "etosEkdoshs": clean_numeric_or_text(row.get('ΕΤΟΣ ΕΚΔΟΣΗΣ')),
                                "toposEkdoshs": clean(row.get('ΤΟΠΟΣ  ΕΚΔΟΣΗΣ')),
                                "sxhma": clean(row.get('ΣΧΗΜΑ')),
                                "selides": clean(row.get('ΣΕΛΙΔΕΣ')),
                                "tomos": clean(row.get('ΤΟΜΟΣ')),
                                "troposPromPar": clean(row.get('ΤΡΟΠΟΣ ΠΡΟΜΗΘΕΙΑΣ ΠΑΡΑΤΗΡΗΣΕΙΣ')),
                                "ISBN": clean_numeric_or_text(row.get('ISBN')),
                                "sthlh1": clean_numeric_or_text(row.get('Στήλη1')),
                                "sthlh2": clean_numeric_or_text(row.get('Στήλη2')),
                            },
                        })
                        continue

                    # Πραγματικό duplicate → αποθήκευση για resolve
                    duplicates.append({
                        "left": {
                            "ari8mos": existing_person.ari8mosEisagoghs,
                            "hmeromhnia_eis": existing_person.hmeromhnia_eis,
                            "syggrafeas": existing_person.syggrafeas,
                            "koha": existing_person.koha,
                            "titlos": existing_person.titlos,
                            "ekdoths": existing_person.ekdoths,
                            "ekdosh": existing_person.ekdosh,
                            "etosEkdoshs": existing_person.etosEkdoshs,
                            "toposEkdoshs": existing_person.toposEkdoshs,
                            "sxhma": existing_person.sxhma,
                            "selides": existing_person.selides,
                            "tomos": existing_person.tomos,
                            "troposPromPar": existing_person.troposPromPar,
                            "ISBN": existing_person.ISBN,
                            "sthlh1": existing_person.sthlh1,
                            "sthlh2": existing_person.sthlh2,
                        },
                        "right": {
                            "ari8mos": ari8mos,
                            "hmeromhnia_eis": clean_numeric_or_text(row.get('ΗΜΕΡΟΜΗΝΙΑ ΕΙΣΑΓΩΓΗΣ')),
                            "syggrafeas": clean(row.get('ΣΥΓΓΡΑΦΕΑΣ')),
                            "koha": koha,
                            "titlos": clean(row.get('ΤΙΤΛΟΣ')),
                            "ekdoths": clean(row.get('ΕΚΔΟΤΗΣ')),
                            "ekdosh": clean(row.get('ΕΚΔΟΣΗ')),
                            "etosEkdoshs": clean_numeric_or_text(row.get('ΕΤΟΣ ΕΚΔΟΣΗΣ')),
                            "toposEkdoshs": clean(row.get('ΤΟΠΟΣ  ΕΚΔΟΣΗΣ')),
                            "sxhma": clean(row.get('ΣΧΗΜΑ')),
                            "selides": clean(row.get('ΣΕΛΙΔΕΣ')),
                            "tomos": clean(row.get('ΤΟΜΟΣ')),
                            "troposPromPar": clean(row.get('ΤΡΟΠΟΣ ΠΡΟΜΗΘΕΙΑΣ ΠΑΡΑΤΗΡΗΣΕΙΣ')),
                            "ISBN": clean_numeric_or_text(row.get('ISBN')),
                            "sthlh1": clean_numeric_or_text(row.get('Στήλη1')),
                            "sthlh2": clean_numeric_or_text(row.get('Στήλη2')),
                        },
                    })
                    continue

                # ✅ SAFE INSERT
                new_objects.append(Person(
                    ari8mosEisagoghs=ari8mos,
                    hmeromhnia_eis=clean_numeric_or_text(row.get('ΗΜΕΡΟΜΗΝΙΑ ΕΙΣΑΓΩΓΗΣ')),
                    syggrafeas=clean(row.get('ΣΥΓΓΡΑΦΕΑΣ')),
                    koha=koha,
                    titlos=clean(row.get('ΤΙΤΛΟΣ')),
                    ekdoths=clean(row.get('ΕΚΔΟΤΗΣ')),
                    ekdosh=clean(row.get('ΕΚΔΟΣΗ')),
                    etosEkdoshs=clean_numeric_or_text(row.get('ΕΤΟΣ ΕΚΔΟΣΗΣ')),
                    toposEkdoshs=clean(row.get('ΤΟΠΟΣ  ΕΚΔΟΣΗΣ')),
                    sxhma=clean(row.get('ΣΧΗΜΑ')),
                    selides=clean(row.get('ΣΕΛΙΔΕΣ')),
                    tomos=clean(row.get('ΤΟΜΟΣ')),
                    troposPromPar=clean(row.get('ΤΡΟΠΟΣ ΠΡΟΜΗΘΕΙΑΣ ΠΑΡΑΤΗΡΗΣΕΙΣ')),
                    ISBN=clean_numeric_or_text(row.get('ISBN')),
                    sthlh1=clean_numeric_or_text(row.get('Στήλη1')),
                    sthlh2=clean_numeric_or_text(row.get('Στήλη2')),
                ))
                existing_ids.add(ari8mos)
                
                added.append({
                    'ari8mos': ari8mos,
                    'titlos': clean(row.get('ΤΙΤΛΟΣ')),
                    'syggrafeas': clean(row.get('ΣΥΓΓΡΑΦΕΑΣ')),
                })
           
            # ✅ Bulk create new records (non-duplicates)
            Person.objects.bulk_create(new_objects, batch_size=1000)

            # ✅ Store data in session for duplicate resolution
            request.session['duplicates'] = duplicates
            request.session['potential_insertions'] = potential_insertions
            request.session['new_records_count'] = len(new_objects)
            request.session['skipped_count'] = len(skipped)

            # ✅ If there are duplicates or potential insertions, redirect to resolution page
            if duplicates or potential_insertions:
                return redirect('resolve_duplicates')

            # ✅ Log upload
            UploadLog.objects.create(
                user=request.user,
                filename=excel_file.name,
                rows_added=len(new_objects),
                rows_updated=0,
            )

            total_records = Person.objects.count()

            # No duplicates, go straight to results
            return render(request, 'upload_result.html', {
                'added_count': len(new_objects),
                'duplicate_count': 0,
                'skipped_count': len(skipped),
                'total_records': total_records,
            })

    else:
        form = UploadExcelForm()

    return render(request, 'upload_excel.html', {'form': form})



@login_required
def resolve_duplicates(request):
    """Show all duplicates and potential insertions for user to review"""
    duplicates = request.session.get('duplicates', [])  # Changed from 'main/duplicates'
    potential_insertions = request.session.get('potential_insertions', [])
    
    if not duplicates and not potential_insertions:
        messages.info(request, 'No duplicates or potential insertions to resolve.')
        return redirect('upload_excel')
    
    return render(request, 'main/resolve_duplicates.html', {  # Make sure path is correct
        'duplicates': duplicates,
        'potential_insertions': potential_insertions,
        'duplicate_count': len(duplicates),
        'insertion_count': len(potential_insertions),
    })

@login_required
def replace_all_duplicates(request):
    """Replace selected database records with Excel data"""
    if request.method == 'POST':
        duplicates = request.session.get('duplicates', [])  # Changed from 'main/duplicates'
        potential_insertions = request.session.get('potential_insertions', [])
        
        # Get selected IDs from POST data
        selected_duplicate_ids = request.POST.getlist('duplicate_ids[]')
        selected_insertion_ids = request.POST.getlist('insertion_ids[]')
        
        updated_count = 0
        inserted_count = 0
        
        # Handle selected duplicates
        for dup in duplicates:
            ari8mos = str(dup['left']['ari8mos'])
            
            # Only process if selected
            if ari8mos not in selected_duplicate_ids:
                continue
            
            try:
                person = Person.objects.get(ari8mosEisagoghs=int(ari8mos))
                
                # Update with Excel data (from 'right')
                person.hmeromhnia_eis = dup['right']['hmeromhnia_eis']
                person.syggrafeas = dup['right']['syggrafeas']
                person.koha = dup['right']['koha']
                person.titlos = dup['right']['titlos']
                person.ekdoths = dup['right']['ekdoths']
                person.ekdosh = dup['right']['ekdosh']
                person.etosEkdoshs = dup['right']['etosEkdoshs']
                person.toposEkdoshs = dup['right']['toposEkdoshs']
                person.sxhma = dup['right']['sxhma']
                person.selides = dup['right']['selides']
                person.tomos = dup['right']['tomos']
                person.troposPromPar = dup['right']['troposPromPar']
                person.ISBN = dup['right']['ISBN']
                person.sthlh1 = dup['right']['sthlh1']
                person.sthlh2 = dup['right']['sthlh2']
                
                person.save()
                updated_count += 1
                
            except Person.DoesNotExist:
                continue
        
        # Handle selected potential insertions (empty records)
        for insertion in potential_insertions:
            ari8mos = str(insertion['ari8mos'])
            
            # Only process if selected
            if ari8mos not in selected_insertion_ids:
                continue
            
            try:
                person = Person.objects.get(ari8mosEisagoghs=int(ari8mos))
                
                # Fill empty record with Excel data
                person.hmeromhnia_eis = insertion['excel']['hmeromhnia_eis']
                person.syggrafeas = insertion['excel']['syggrafeas']
                person.koha = insertion['excel']['koha']
                person.titlos = insertion['excel']['titlos']
                person.ekdoths = insertion['excel']['ekdoths']
                person.ekdosh = insertion['excel']['ekdosh']
                person.etosEkdoshs = insertion['excel']['etosEkdoshs']
                person.toposEkdoshs = insertion['excel']['toposEkdoshs']
                person.sxhma = insertion['excel']['sxhma']
                person.selides = insertion['excel']['selides']
                person.tomos = insertion['excel']['tomos']
                person.troposPromPar = insertion['excel']['troposPromPar']
                person.ISBN = insertion['excel']['ISBN']
                person.sthlh1 = insertion['excel']['sthlh1']
                person.sthlh2 = insertion['excel']['sthlh2']
                
                person.save()
                inserted_count += 1
                
            except Person.DoesNotExist:
                continue
        
        # Get counts from session
        new_records_count = request.session.get('new_records_count', 0)
        skipped_count = request.session.get('skipped_count', 0)
        
        # Log upload
        UploadLog.objects.create(
            user=request.user,
            filename='Excel Upload',
            rows_added=new_records_count,
            rows_updated=updated_count + inserted_count,
        )
        
        # Clear session
        request.session.pop('duplicates', None)
        request.session.pop('potential_insertions', None)
        request.session.pop('new_records_count', None)
        request.session.pop('skipped_count', None)
        
        total_records = Person.objects.count()
        
        if updated_count > 0 or inserted_count > 0:
            messages.success(request, f'Successfully replaced {updated_count} duplicates and filled {inserted_count} empty records!')
        else:
            messages.info(request, 'No records were updated.')
        
        return render(request, 'upload_result.html', {
            'added_count': new_records_count,
            'updated_count': updated_count + inserted_count,
            'duplicate_count': 0,
            'skipped_count': skipped_count,
            'total_records': total_records,
        })
    
    return redirect('resolve_duplicates')

@login_required
def skip_all_duplicates(request):
    """Skip all duplicates and insertions - keep database records as they are"""
    if request.method == 'POST':
        duplicates = request.session.get('duplicates', [])  # Changed from 'main/duplicates'
        potential_insertions = request.session.get('potential_insertions', [])
        new_records_count = request.session.get('new_records_count', 0)
        skipped_count = request.session.get('skipped_count', 0)
        
        # Log upload
        UploadLog.objects.create(
            user=request.user,
            filename='Excel Upload',
            rows_added=new_records_count,
            rows_updated=0,
        )
        
        # Clear session
        request.session.pop('duplicates', None)
        request.session.pop('potential_insertions', None)
        request.session.pop('new_records_count', None)
        request.session.pop('skipped_count', None)
        
        total_records = Person.objects.count()
        
        total_skipped = len(duplicates) + len(potential_insertions)
        
        messages.info(request, f'Skipped {total_skipped} records (duplicates and empty records). Database unchanged.')
        
        return render(request, 'upload_result.html', {
            'added_count': new_records_count,
            'updated_count': 0,
            'duplicate_count': 0,
            'skipped_count': skipped_count + total_skipped,
            'total_records': total_records,
        })
    
    return redirect('resolve_duplicates')




# ———————————————— Υπόλοιπες view functions παραμένουν ίδιες ————————————————



@login_required
def edit_person(request, ari8mos):
    """Edit an existing person record"""
    person = get_object_or_404(Person, ari8mosEisagoghs=ari8mos)
    
    if request.method == 'POST':
        form = PersonManualForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, f'Record #{ari8mos} updated successfully!')
            return redirect('show_people')
    else:
        form = PersonManualForm(instance=person)
    
    return render(request, 'main/edit_person.html', {
        'form': form,
        'person': person,
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)    
def delete_person(request, ari8mos):
    """Delete a person record"""
    person = get_object_or_404(Person, ari8mosEisagoghs=ari8mos)
    
    if request.method == 'POST':
        person.delete()
        messages.success(request, f'Record #{ari8mos} deleted successfully!')
        return redirect('show_people')
    
    return HttpResponseForbidden("You are not allowed to delete records.")

class RegexpReplace(Func):
    function = 'REGEXP_REPLACE'
    arity = 3

@login_required
def add_person(request):
    last_number = (
        Person.objects
        .exclude(ari8mosEisagoghs__isnull=True)
        .aggregate(max_num=Max("ari8mosEisagoghs"))
        ["max_num"]
    )

    next_number = (last_number or 0) + 1
    
    # ✅ Check if we're filling an incomplete record
    prefill_ari8mos = request.GET.get("ari8mos")

    # ✅ FLAG ΑΠΟ REDIRECT
    submitted = request.GET.get("submitted") == "1"

    if request.method == 'POST':
        form = PersonManualForm(request.POST)
        if form.is_valid():
            person = form.save(commit=False)
            
            # ✅ Track if we're updating an incomplete record
            was_filling_incomplete = bool(prefill_ari8mos)
            
            # ✅ If updating an existing record, use that ari8mos
            if prefill_ari8mos:
                person.ari8mosEisagoghs = int(prefill_ari8mos)
            else:
                person.ari8mosEisagoghs = next_number
            
            person.save()
            
            # ✅ If we were filling incomplete records, redirect to the next one
            if was_filling_incomplete:
                next_incomplete = Person.objects.filter(
                    Q(syggrafeas__isnull=True) &
                    Q(koha__isnull=True) &
                    Q(titlos__isnull=True) &
                    Q(ekdoths__isnull=True) &
                    Q(ekdosh__isnull=True) &
                    Q(etosEkdoshs__isnull=True) &
                    Q(toposEkdoshs__isnull=True) &
                    Q(sxhma__isnull=True) &
                    Q(selides__isnull=True) &
                    Q(tomos__isnull=True) &
                    #Q(troposPromPar__isnull=True) &
                    Q(ISBN__isnull=True) &
                    Q(sthlh1__isnull=True) &
                    Q(sthlh2__isnull=True)
                ).order_by('ari8mosEisagoghs').first()
                
                if next_incomplete:
                    # Redirect to next incomplete record
                    return redirect(f"{reverse('add_person')}?ari8mos={next_incomplete.ari8mosEisagoghs}&submitted=1")
                else:
                    # No more incomplete records, show completion message
                    return redirect(f"{reverse('add_person')}?submitted=1&all_complete=1")
                
            # ✅ POST → REDIRECT → GET
            return redirect(f"{reverse('add_person')}?submitted=1")
    else:
         # ✅ Pre-fill the form if ari8mos is provided
        if prefill_ari8mos:
            try:
                existing_person = Person.objects.get(ari8mosEisagoghs=int(prefill_ari8mos))
                form = PersonManualForm(instance=existing_person)
            except Person.DoesNotExist:
                form = PersonManualForm()
                
        else:        
          form = PersonManualForm()

    return render(
        request,
        'main/add_person.html',
        {
            'form': form,
            'next_number': prefill_ari8mos or next_number,
            'submitted': submitted,
            'is_editing': bool(prefill_ari8mos),  # Flag to show user they're editing
            'all_complete': request.GET.get('all_complete') == '1',  # New flag
        }
    )

@login_required
def print_range(request):
    """Print a range of records"""
    from_num = request.GET.get('from_num')
    to_num = request.GET.get('to_num')
    
    if not from_num or not to_num:
        messages.error(request, 'Παρακαλώ εισάγετε έγκυρο αριθμό αφετηρίας και τέλους')
        return redirect('show_people')
    
    try:
        from_num = int(from_num)
        to_num = int(to_num)
    except ValueError:
        messages.error(request, 'Άκυρο εύρος αριθμών.')
        return redirect('show_people')
    
     # Calculate total count
    total_count = Person.objects.filter(
        ari8mosEisagoghs__gte=from_num,
        ari8mosEisagoghs__lte=to_num
    ).count()
    
    return render(request, 'main/print_range.html', {
        'from_num': from_num,
        'to_num': to_num,
        'total_count': total_count,
    })


@login_required
def print_range_data(request):
    """API endpoint to fetch records in batches"""
    from_num = request.GET.get('from_num')
    to_num = request.GET.get('to_num')
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 100))
    
    try:
        from_num = int(from_num)
        to_num = int(to_num)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    
    # Fetch a batch of records
    records = Person.objects.filter(
        ari8mosEisagoghs__gte=from_num,
        ari8mosEisagoghs__lte=to_num
    ).order_by('ari8mosEisagoghs')[offset:offset + limit]
    
    # Convert to list of dicts
    data = []
    for person in records:
        data.append({
            'ari8mosEisagoghs': person.ari8mosEisagoghs,
            'hmeromhnia_eis': person.hmeromhnia_eis or '-',
            'syggrafeas': person.syggrafeas or '-',
            'koha': person.koha or '-',
            'titlos': person.titlos or '-',
            'ekdoths': person.ekdoths or '-',
            'ekdosh': person.ekdosh or '-',
            'etosEkdoshs': person.etosEkdoshs or '-',
            'toposEkdoshs': person.toposEkdoshs or '-',
            'sxhma': person.sxhma or '-',
            'selides': person.selides or '-',
            'tomos': person.tomos or '-',
            'ISBN': person.ISBN or '-',
        })
    
    return JsonResponse({
        'records': data,
        'has_more': len(records) == limit
    })


